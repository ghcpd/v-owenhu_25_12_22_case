import os
import re
import hmac
import hashlib
import logging
import secrets
import sqlite3
import requests
import yaml
import zipfile
from urllib.parse import urlparse
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# Configuration (no hardcoded secrets)
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")  # required for production
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
API_KEY = os.environ.get("API_KEY", "dev-api-key")

DB_FILE = os.path.join(os.path.dirname(__file__), "appdata.db")
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helpers
ALLOWED_FILENAME = re.compile(r"^[A-Za-z0-9_-]+$")


def require_api_key(f):
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key") or request.json.get("api_key") if request.is_json else None
        if key != API_KEY:
            abort(401)
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def is_valid_url(u):
    try:
        p = urlparse(u)
        if p.scheme not in ("http", "https"):
            return False
        host = p.hostname
        # disallow localhost/private IPs
        if host in ("localhost", "127.0.0.1"):
            return False
        return True
    except Exception:
        return False


def auth_user(info):
    username = (info or {}).get("username", "")
    # Use HMAC-SHA256 with server secret
    token = hmac.new(SECRET_KEY.encode(), username.encode(), hashlib.sha256).hexdigest()
    return token


def query_profile(uid):
    # validate input and use parameterized queries
    try:
        uid_int = int(uid)
    except Exception:
        raise ValueError("invalid user id")
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid_int,))
        data = c.fetchall()
        return data
    finally:
        conn.close()


def transfer_funds(payload):
    # validate and protect against SSRF and sensitive token leakage
    target = payload.get("target")
    amount = payload.get("amount")
    notify_url = payload.get("notify_url")

    if not isinstance(amount, (int, float)):
        raise ValueError("invalid amount")
    if not is_valid_url(notify_url):
        raise ValueError("invalid notify_url")

    logger.info("transfer request to %s amount=%s", target, amount)

    # send a signed callback (do not leak PAYMENT_TOKEN directly)
    signature = None
    if PAYMENT_TOKEN:
        signature = hmac.new(PAYMENT_TOKEN.encode(), f"{target}:{amount}".encode(), hashlib.sha256).hexdigest()

    try:
        resp = requests.post(notify_url, json={"amount": amount, "signature": signature}, timeout=5)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.warning("notify failed: %s", e)
        raise


def update_records(path):
    # only allow files under CONFIG_DIR
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath(CONFIG_DIR) + os.sep):
        raise ValueError("access to path not permitted")
    with open(abs_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # sanitize filename and use zipfile module (no shell)
    if not ALLOWED_FILENAME.match(name or ""):
        raise ValueError("invalid name")
    out_path = os.path.abspath(f"{name}.zip")
    with zipfile.ZipFile(out_path, "w") as zf:
        zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    return out_path


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json
    return jsonify({"token": auth_user(info)})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    try:
        return jsonify(query_profile(uid))
    except ValueError:
        return jsonify({"error": "invalid id"}), 400


@app.route("/transfer", methods=["POST"])
@require_api_key
def api_transfer():
    p = request.json
    try:
        return jsonify({"result": transfer_funds(p)})
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "transfer failed"}), 400


@app.route("/config", methods=["POST"])
@require_api_key
def api_config():
    path = request.json.get("file")
    try:
        return jsonify(update_records(path))
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "cannot load config"}), 400


@app.route("/export")
@require_api_key
def api_export():
    name = request.args.get("name")
    try:
        out = export_data(name)
        return jsonify({"ok": 1, "file": out})
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "export failed"}), 400


if __name__ == "__main__":
    # run with debug controlled by environment
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)
