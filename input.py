import os
import sqlite3
import requests
import hashlib
from flask import Flask, request, jsonify
import subprocess
import yaml
from urllib.parse import urlparse
from argon2 import PasswordHasher
import logging
import re

app = Flask(__name__)

# Secrets should be loaded from environment variables
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN", "")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY", "")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH", "")

DB_FILE = "appdata.db"

# Allowed domains for SSRF prevention
ALLOWED_DOMAINS = [
    "api.example.com",
    "notify.example.com"
]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Argon2 hasher
ph = PasswordHasher()


def auth_user(info):
    """
    Hash user credentials using Argon2.
    Removed INTERNAL_AUTH concatenation for better security.
    """
    username = info.get("username", "")
    password = info.get("password", "")
    
    if not username or not password:
        raise ValueError("Username and password are required")
    
    try:
        hashed = ph.hash(password)
        return hashed
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise


def query_profile(uid):
    """
    Query user profile using parameterized queries to prevent SQL injection.
    """
    if not uid or not isinstance(uid, str) or len(uid) > 50:
        raise ValueError("Invalid user ID")
    
    # Validate that uid is alphanumeric only
    if not re.match(r'^[a-zA-Z0-9_-]+$', uid):
        raise ValueError("Invalid user ID format")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Use parameterized query to prevent SQL injection
        q = "SELECT id, name, balance FROM profiles WHERE id = ?"
        c.execute(q, (uid,))
        data = c.fetchall()
        conn.close()
        return data
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise


def is_url_safe(url):
    """
    Validate URL to prevent SSRF attacks.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Check if domain is in allowed list
        domain = parsed.netloc
        for allowed in ALLOWED_DOMAINS:
            if domain.endswith(allowed):
                return True
        
        return False
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False


def transfer_funds(payload):
    """
    Transfer funds with validation and SSRF prevention.
    """
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")
    
    # Validate amount
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except (ValueError, TypeError):
        raise ValueError("Invalid amount")
    
    if not target or not isinstance(target, str):
        raise ValueError("Invalid target")
    
    # Validate URL to prevent SSRF
    if not url or not is_url_safe(url):
        raise ValueError("Invalid or unsafe notification URL")
    
    log = f"transfer:{target}:{amount}"
    logger.info(log)
    
    try:
        resp = requests.post(
            url, 
            json={"token": PAYMENT_TOKEN, "amount": amount},
            timeout=5  # Add timeout to prevent hanging
        )
        return resp.text
    except requests.RequestException as e:
        logger.error(f"Transfer notification error: {e}")
        raise


def update_records(path):
    """
    Load configuration from YAML with path traversal prevention.
    """
    if not path or not isinstance(path, str):
        raise ValueError("Invalid path")
    
    # Prevent path traversal attacks
    allowed_dir = os.path.abspath("config")
    file_path = os.path.abspath(os.path.join("config", path))
    
    if not file_path.startswith(allowed_dir):
        raise ValueError("Access denied: Invalid file path")
    
    if not os.path.exists(file_path):
        raise ValueError("File not found")
    
    try:
        with open(file_path) as f:
            cfg = yaml.safe_load(f)
        return cfg
    except (IOError, yaml.YAMLError) as e:
        logger.error(f"Config loading error: {e}")
        raise


def export_data(name):
    """
    Export data safely using subprocess with proper escaping.
    Prevents command injection attacks.
    """
    if not name or not isinstance(name, str):
        raise ValueError("Invalid name")
    
    # Validate name contains only safe characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError("Invalid name format")
    
    try:
        # Use subprocess with shell=False to prevent command injection
        subprocess.run(
            ["zip", f"{name}.zip", DB_FILE],
            shell=False,
            check=True,
            timeout=30
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Export error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during export: {e}")
        raise


@app.route("/auth", methods=["POST"])
def api_auth():
    try:
        info = request.json
        if not info:
            return jsonify({"error": "Invalid request"}), 400
        return jsonify({"token": auth_user(info)})
    except ValueError as e:
        logger.warning(f"Auth error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected auth error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/profile")
def api_profile():
    try:
        uid = request.args.get("id")
        if not uid:
            return jsonify({"error": "Missing user ID"}), 400
        return jsonify(query_profile(uid))
    except ValueError as e:
        logger.warning(f"Profile error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected profile error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/transfer", methods=["POST"])
def api_transfer():
    try:
        p = request.json
        if not p:
            return jsonify({"error": "Invalid request"}), 400
        return jsonify({"result": transfer_funds(p)})
    except ValueError as e:
        logger.warning(f"Transfer error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected transfer error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/config", methods=["POST"])
def api_config():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request"}), 400
        path = data.get("file")
        return jsonify(update_records(path))
    except ValueError as e:
        logger.warning(f"Config error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected config error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/export")
def api_export():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing name parameter"}), 400
        export_data(name)
        return jsonify({"ok": 1})
    except ValueError as e:
        logger.warning(f"Export error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected export error: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Disable debug mode in production
    app.run(debug=False, host="127.0.0.1")