"""Generic authentication helpers for the reusable chat web UI.

Supported modes:
  1. Shared secret key: simple admin access for small/internal deployments.
  2. External SSO placeholder: routes are provided so adopters can wire their
     own OIDC/SAML/device-code login without changing the app surface.

Session tokens are Fernet-encrypted JSON stored in an HTTP-only cookie.
Login audit data is stored in a local SQLite database.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

log = logging.getLogger(__name__)

STATE_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")

SECRETS_DIR = Path(os.getenv("CHAT_UI_SECRETS_DIR", "/app/secrets"))
MASTER_KEY_FILE = Path(os.getenv("CHAT_UI_MASTER_KEY_FILE", str(SECRETS_DIR / "master.key")))
ADMIN_KEY_FILE = Path(os.getenv("CHAT_UI_ADMIN_KEY_FILE", str(SECRETS_DIR / "admin_secret.enc")))
STATE_DIR = Path(os.getenv("CHAT_UI_STATE_DIR", "/app/.local_state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)
AUTH_DB_FILE = Path(os.getenv("CHAT_UI_AUTH_DB", str(STATE_DIR / "users.db")))

AUTH_COOKIE = os.getenv("CHAT_UI_AUTH_COOKIE", "chat_auth_token")
SESSION_TTL_SECS = int(os.getenv("CHAT_UI_SESSION_TTL_SECS", "28800"))
SSO_ENABLED = os.getenv("CHAT_UI_SSO_ENABLED", "false").lower() == "true"


def _load_fernet() -> Optional[Fernet]:
    try:
        return Fernet(MASTER_KEY_FILE.read_bytes().strip())
    except Exception as exc:
        log.error("auth: cannot read master key: %s", exc)
        return None


def _get_admin_secret() -> Optional[str]:
    configured = os.getenv("CHAT_UI_ADMIN_SECRET")
    if configured:
        return configured

    fernet = _load_fernet()
    if not fernet:
        return None
    try:
        encrypted = ADMIN_KEY_FILE.read_bytes().strip()
        return fernet.decrypt(encrypted).decode()
    except Exception as exc:
        log.error("auth: cannot decrypt admin secret: %s", exc)
        return None


def create_session_token(user_id: str, tier: str, display_name: str = "") -> Optional[str]:
    fernet = _load_fernet()
    if not fernet:
        return None
    payload = json.dumps({
        "user_id": user_id,
        "tier": tier,
        "display_name": display_name,
        "exp": int(time.time()) + SESSION_TTL_SECS,
    }).encode()
    return fernet.encrypt(payload).decode()


def decode_session_token(token: str) -> Optional[dict]:
    fernet = _load_fernet()
    if not fernet:
        return None
    try:
        data = json.loads(fernet.decrypt(token.encode()).decode())
        if time.time() > data.get("exp", 0):
            return None
        return data
    except (InvalidToken, Exception):
        return None


def _init_db() -> None:
    try:
        con = sqlite3.connect(AUTH_DB_FILE)
        con.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                display_name TEXT,
                tier TEXT NOT NULL,
                auth_method TEXT NOT NULL,
                ip_address TEXT,
                login_time TEXT NOT NULL,
                last_activity TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS approved_users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT,
                tier TEXT NOT NULL DEFAULT 'admin',
                auth_method TEXT,
                first_approved TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS sso_pending (
                state TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                success INTEGER NOT NULL DEFAULT 0,
                user_id TEXT,
                display_name TEXT,
                tier TEXT,
                error TEXT
            )
        """)
        con.commit()
        con.close()
    except Exception as exc:
        log.warning("auth: could not init audit DB: %s", exc)


def record_login(user_id: str, display_name: str, tier: str, auth_method: str, ip: str) -> None:
    try:
        _init_db()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        con = sqlite3.connect(AUTH_DB_FILE)
        con.execute(
            "INSERT INTO user_sessions (user_id, display_name, tier, auth_method, ip_address, login_time, last_activity) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, display_name, tier, auth_method, ip, now, now),
        )
        con.commit()
        con.close()
    except Exception as exc:
        log.warning("auth: could not record login: %s", exc)


def save_approved_user(user_id: str, display_name: str, tier: str, auth_method: str) -> None:
    try:
        _init_db()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        con = sqlite3.connect(AUTH_DB_FILE)
        con.execute(
            """
            INSERT INTO approved_users (user_id, display_name, tier, auth_method, first_approved, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                display_name = excluded.display_name,
                tier = excluded.tier,
                auth_method = excluded.auth_method,
                last_seen = excluded.last_seen
            """,
            (user_id, display_name, tier, auth_method, now, now),
        )
        con.commit()
        con.close()
    except Exception as exc:
        log.warning("auth: could not save approved user: %s", exc)


def get_all_approved_users() -> list[dict]:
    try:
        _init_db()
        con = sqlite3.connect(AUTH_DB_FILE)
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM approved_users ORDER BY last_seen DESC").fetchall()
        con.close()
        return [dict(row) for row in rows]
    except Exception as exc:
        log.warning("auth: could not list approved users: %s", exc)
        return []


def get_active_sessions() -> list[dict]:
    try:
        _init_db()
        cutoff = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(time.time()) - SESSION_TTL_SECS))
        con = sqlite3.connect(AUTH_DB_FILE)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM user_sessions WHERE last_activity >= ? ORDER BY login_time DESC LIMIT 50",
            (cutoff,),
        ).fetchall()
        con.close()
        return [dict(row) for row in rows]
    except Exception as exc:
        log.warning("auth: could not query sessions: %s", exc)
        return []


def sso_configured() -> bool:
    return SSO_ENABLED


def sso_start() -> dict:
    if not sso_configured():
        return {"error": "SSO is not configured for this deployment."}
    return {"error": "SSO start is a template hook. Wire this function to your identity provider."}


def sso_poll(state: str) -> dict:
    if not STATE_RE.fullmatch(state or ""):
        return {"done": False, "just_completed": False}
    return {"done": False, "just_completed": False, "error": "SSO polling is not implemented."}


@dataclass
class AuthResult:
    success: bool
    tier: str = "user"
    user_id: str = ""
    display_name: str = ""
    method: str = ""
    error: str = ""


def authenticate(user_id: str, password: str, secret_key: str = "") -> AuthResult:
    del password
    if secret_key:
        admin_secret = _get_admin_secret()
        if admin_secret and secret_key.strip() == admin_secret.strip():
            uid = user_id or "key-user"
            save_approved_user(uid, uid, "admin", "secret_key")
            return AuthResult(True, "admin", uid, uid, "secret_key")
        return AuthResult(False, error="Invalid secret key", method="secret_key")
    return AuthResult(False, error="Use SSO or a valid secret key.", method="none")