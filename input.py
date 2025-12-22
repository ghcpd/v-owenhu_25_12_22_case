import os
import re
import sqlite3
import requests
import hashlib
import hmac
import logging
import zipfile
from urllib.parse import urlparse
from flask import Flask, request, jsonify, abort
import yaml

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Secrets must be provided via environment variables in production
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH_SECRET = os.environ.get("INTERNAL_AUTH_SECRET")

# Optional: comma-separated list of hosts allowed for notifications (for SSRF protection)
ALLOWED_NOTIFY_HOSTS = os.environ.get("ALLOWED_NOTIFY_HOSTS", "localhost,127.0.0.1").split(",")

DB_FILE = os.environ.get("DB_FILE", "appdata.db")
CONFIG_DIR = os.environ.get("CONFIG_DIR", "configs")

NAME_SAFE_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


def require_api_key(f):
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        if not key or key != INTERNAL_AUTH_SECRET:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def auth_user(info):
    username = info.get("username", "")
    if not username or not INTERNAL_AUTH_SECRET:
        abort(400, "invalid credentials")
    # Use HMAC with SHA256 instead of MD5
    token = hmac.new(INTERNAL_AUTH_SECRET.encode(), username.encode(), hashlib.sha256).hexdigest()
    return token


def query_profile(uid):
    if not uid or not uid.isdigit():
        return []
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    q = "SELECT id, name, balance FROM profiles WHERE id = ?"
    c.execute(q, (int(uid),))
    data = c.fetchall()
    conn.close()
    return data


def transfer_funds(payload):
    # Validate payload fields
    try:
        target = str(payload.get("target"))
        amount = float(payload.get("amount"))
    except Exception:
        raise ValueError("invalid transfer payload")
    if amount <= 0:
        raise ValueError("amount must be positive")

    url = payload.get("notify_url")
    if not url:
        raise ValueError("notify_url required")

    # Basic URL validation to prevent SSRF
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("invalid notify_url")

    hostname = parsed.hostname
    if hostname not in ALLOWED_NOTIFY_HOSTS:
        raise ValueError("notify host not allowed")

    headers = {"Authorization": f"Bearer {PAYMENT_TOKEN}"} if PAYMENT_TOKEN else {}
    try:
        resp = requests.post(url, json={"amount": amount}, headers=headers, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.exception("notify request failed")
        raise
    return resp.text


def update_records(path):
    # Restrict file reads to a safe configuration directory
    if not path:
        raise ValueError("file path required")
    base = os.path.basename(path)
    safe_path = os.path.join(CONFIG_DIR, base)
    if not os.path.exists(safe_path):
        raise FileNotFoundError("config not found")
    with open(safe_path, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Create zip using Python stdlib (no shell invocation)
    if not name or not NAME_SAFE_RE.match(name):
        raise ValueError("invalid name")
    zip_name = f"{name}.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DB_FILE)
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    token = auth_user(info)
    return jsonify({"token": token})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    try:
        data = query_profile(uid)
    except Exception:
        return jsonify({}), 400
    return jsonify(data)


@app.route("/transfer", methods=["POST"])
@require_api_key
def api_transfer():
    p = request.json or {}
    try:
        result = transfer_funds(p)
    except Exception as e:
        logging.exception("transfer failed")
        return jsonify({"error": str(e)}), 400
    return jsonify({"result": result})


@app.route("/config", methods=["POST"])
@require_api_key
def api_config():
    path = (request.json or {}).get("file")
    try:
        cfg = update_records(path)
    except Exception as e:
        logging.exception("config update failed")
        return jsonify({"error": str(e)}), 400
    return jsonify(cfg)


@app.route("/export")
@require_api_key
def api_export():
    name = request.args.get("name")
    try:
        export_data(name)
    except Exception as e:
        logging.exception("export failed")
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": 1})


if __name__ == "__main__":
    # Do not run Flask in debug mode in production
    app.run(host="0.0.0.0", debug=False)