import os
import re
import hmac
import json
import sqlite3
import logging
import hashlib
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

import requests
import yaml
from flask import Flask, request, jsonify, abort

# --- configuration (required via environment) ------------------------------
APP_DIR = Path(__file__).parent
DB_FILE = Path(os.getenv("DB_FILE", APP_DIR / "appdata.db"))
EXPORT_DIR = Path(os.getenv("EXPORT_DIR", APP_DIR / "exports"))
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", APP_DIR / "configs"))
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# required secrets (must be set in environment for secure operation)
AUTH_SECRET = os.getenv("AUTH_SECRET")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")  # used for sensitive endpoints

if not AUTH_SECRET or not PAYMENT_TOKEN:
    # fail fast in non-test/CI environments
    logging.warning("AUTH_SECRET or PAYMENT_TOKEN not set — service will run in degraded mode for local testing")

# allowed hosts for outgoing notifications (comma-separated); defaults to localhost only
ALLOWED_NOTIFY_HOSTS = set(h.strip() for h in os.getenv("ALLOWED_NOTIFY_HOSTS", "localhost,127.0.0.1").split(","))

# logger
logger = logging.getLogger("secure_app")
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- helpers ---------------------------------------------------------------

NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _require_admin_key(req: request) -> None:
    key = req.headers.get("X-API-KEY")
    if not ADMIN_API_KEY or not key or not hmac.compare_digest(key, ADMIN_API_KEY):
        abort(401, description="missing or invalid api key")


def _safe_path_in_dir(basedir: Path, filename: str) -> Path:
    if os.path.sep in filename or filename.startswith("."):
        raise ValueError("invalid filename")
    candidate = (basedir / filename).resolve()
    if basedir.resolve() not in candidate.parents and basedir.resolve() != candidate.parent:
        raise ValueError("file outside allowed directory")
    return candidate


def _is_allowed_notify_url(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = p.hostname
    return host in ALLOWED_NOTIFY_HOSTS


def _get_db_conn():
    return sqlite3.connect(str(DB_FILE))


# --- application logic (secure replacements) -------------------------------


def auth_user(info: dict) -> str:
    """Create an HMAC-SHA256 token for a username. Requires AUTH_SECRET in env.

    Returns hex signature. If AUTH_SECRET is missing (local dev) falls back to
    SHA256(username) but logs a warning.
    """
    username = (info or {}).get("username") or ""
    if not username:
        raise ValueError("username required")
    if AUTH_SECRET:
        sig = hmac.new(AUTH_SECRET.encode(), username.encode(), hashlib.sha256).hexdigest()
        return sig
    # fallback for local/dev only
    logging.warning("AUTH_SECRET not set — using weakened fallback hash")
    return hashlib.sha256(username.encode()).hexdigest()


def query_profile(uid: Optional[str]):
    """Parameterised query. Only integer IDs are accepted."""
    if uid is None:
        raise ValueError("id required")
    # enforce integer id to prevent SQLi
    try:
        uid_int = int(uid)
    except Exception:
        return []
    with _get_db_conn() as conn:
        cur = conn.execute("SELECT id, name, balance FROM profiles WHERE id = ?", (uid_int,))
        return cur.fetchall()


def transfer_funds(payload: dict) -> str:
    target = payload.get("target")
    amount = payload.get("amount")
    notify = payload.get("notify_url")
    logger.info("transfer request: target=%s amount=%s", target, amount)

    # validate inputs
    if not target or not amount:
        raise ValueError("target and amount are required")
    if notify and not _is_allowed_notify_url(notify):
        raise ValueError("notify_url not allowed")

    body = {"amount": amount}
    headers = {"Content-Type": "application/json"}
    # send secret only to allowlisted hosts and using Authorization header
    if notify:
        headers["Authorization"] = f"Bearer {PAYMENT_TOKEN}"
    try:
        resp = requests.post(notify, json=body, headers=headers, timeout=5, verify=True) if notify else None
        return resp.text if resp is not None else "ok"
    except requests.RequestException as e:
        logger.exception("notification failed")
        raise


def update_records(filename: str):
    # only allow files inside CONFIG_DIR by filename
    safe = _safe_path_in_dir(CONFIG_DIR, filename)
    try:
        with safe.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise


def export_data(name: str) -> str:
    # safe name validation and use of zipfile module (no shell)
    if not NAME_RE.match(name):
        raise ValueError("invalid export name")
    out = EXPORT_DIR / f"{name}.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE, arcname=DB_FILE.name)
    return str(out)


# --- HTTP endpoints (safer behaviors) -------------------------------------


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.get_json(force=True, silent=True)
    try:
        token = auth_user(info)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"token": token})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    try:
        return jsonify(query_profile(uid))
    except ValueError:
        return jsonify([]), 400


@app.route("/transfer", methods=["POST"])
def api_transfer():
    p = request.get_json(force=True, silent=True) or {}
    try:
        return jsonify({"result": transfer_funds(p)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/config", methods=["POST"])
def api_config():
    _require_admin_key(request)
    filename = (request.get_json() or {}).get("file")
    return jsonify(update_records(filename))


@app.route("/export")
def api_export():
    _require_admin_key(request)
    name = request.args.get("name")
    path = export_data(name)
    return jsonify({"export": path})


if __name__ == "__main__":
    # never run with debug=True in production; respect env vars for host/port
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    app.run(host=host, port=port, debug=False)
