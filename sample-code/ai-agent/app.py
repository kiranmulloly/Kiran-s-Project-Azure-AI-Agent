"""Generic FastAPI entry point for a reusable agent chat web UI."""

from __future__ import annotations

import asyncio
import html
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

import auth as _auth
from session import ChatSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
AUTH_COOKIE = _auth.AUTH_COOKIE
SESSION_COOKIE = os.getenv("CHAT_UI_SESSION_COOKIE", "chat_session_id")
MAX_SESSIONS = int(os.getenv("CHAT_UI_MAX_SESSIONS", "3"))
SESSION_TTL_SECONDS = int(os.getenv("CHAT_UI_SESSION_TTL_SECONDS", "1800"))
APP_TITLE = os.getenv("CHAT_UI_TITLE", "Agent Chat Web UI")
STATE_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")

AUTH_EXEMPT = {
    "/login",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/sso/start",
    "/api/auth/sso/status",
    "/health",
}

app = FastAPI(title=APP_TITLE)
_sessions: Dict[str, ChatSession] = {}
_sessions_lock = asyncio.Lock()


@app.middleware("http")
async def require_auth(request: Request, call_next):
    path = request.url.path
    if path in AUTH_EXEMPT:
        return await call_next(request)

    token = request.cookies.get(AUTH_COOKIE)
    if token:
        session_data = _auth.decode_session_token(token)
        if session_data:
            request.state.user = session_data
            return await call_next(request)

    if path.startswith("/api/"):
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})
    redirect_url = f"/login?next={request.url.path}"
    if token:
        redirect_url += "&error=3"
    return RedirectResponse(redirect_url, status_code=302)


def _evict_stale() -> None:
    now = datetime.now()
    stale = [
        session_id for session_id, session in _sessions.items()
        if (now - session.last_used).total_seconds() > SESSION_TTL_SECONDS
    ]
    for session_id in stale:
        session = _sessions.pop(session_id)
        asyncio.ensure_future(session.cleanup())


async def _get_or_create(request: Request, response: Response, model: str = "auto") -> ChatSession:
    session_id = request.cookies.get(SESSION_COOKIE)
    async with _sessions_lock:
        _evict_stale()
        if session_id and session_id in _sessions:
            existing = _sessions[session_id]
            if model and model != "auto" and existing.model != model:
                _sessions.pop(session_id, None)
                asyncio.ensure_future(existing.cleanup())
            else:
                return existing

        if len(_sessions) >= MAX_SESSIONS:
            raise HTTPException(status_code=503, detail=f"All {MAX_SESSIONS} session slots are busy.")

        session_id = str(uuid4())
        session = ChatSession(session_id, model=model)
        _sessions[session_id] = session

    response.set_cookie(SESSION_COOKIE, session_id, httponly=True, samesite="lax")
    return session


class LoginRequest(BaseModel):
    user_id: str = ""
    password: str = ""
    secret_key: str = ""


class PromptRequest(BaseModel):
    message: str
    model: str = "auto"


class WarmupRequest(BaseModel):
    model: str = "auto"


class PromptResponse(BaseModel):
    response: str
    timestamp: str
    session_id: str
    model: str = "auto"


@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_html = BASE_DIR / "index.html"
    if index_html.exists():
        return index_html.read_text()
    return HTMLResponse(f"<html><body><h1>{html.escape(APP_TITLE)}</h1></body></html>")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get(AUTH_COOKIE)
    if token and _auth.decode_session_token(token):
        return RedirectResponse("/", status_code=302)
    login_html = BASE_DIR / "login.html"
    if login_html.exists():
        return HTMLResponse(login_html.read_text())
    return HTMLResponse(
        "<html><body><form method='post' action='/api/auth/login'>"
        "<input name='user_id' placeholder='User ID'/>"
        "<input name='secret_key' placeholder='Secret key' type='password'/>"
        "<button type='submit'>Sign in</button>"
        "</form></body></html>"
    )


@app.post("/api/auth/login")
async def api_login(body: LoginRequest, request: Request, response: Response):
    raw_user_id = body.user_id.strip()
    if raw_user_id and not re.fullmatch(r"[A-Za-z0-9_.@-]{1,100}", raw_user_id):
        raise HTTPException(status_code=400, detail="User ID contains invalid characters")

    result = _auth.authenticate(raw_user_id, body.password, body.secret_key.strip())
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error or "Authentication failed")

    token = _auth.create_session_token(result.user_id, result.tier, result.display_name)
    if not token:
        raise HTTPException(status_code=500, detail="Could not create session token")

    ip = request.client.host if request.client else "unknown"
    _auth.record_login(result.user_id, result.display_name, result.tier, result.method, ip)
    response.set_cookie(AUTH_COOKIE, token, httponly=True, samesite="lax", max_age=_auth.SESSION_TTL_SECS)
    return {"ok": True, "tier": result.tier, "redirect": "/"}


@app.post("/api/auth/sso/start")
async def api_sso_start():
    result = await asyncio.to_thread(_auth.sso_start)
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@app.get("/api/auth/sso/status")
async def api_sso_status(state: str, request: Request):
    if not STATE_RE.fullmatch(state):
        raise HTTPException(status_code=400, detail="Invalid SSO state")

    poll = _auth.sso_poll(state)
    response = JSONResponse(poll)
    if poll.get("just_completed") and poll.get("success") and poll.get("user_id"):
        token = _auth.create_session_token(
            poll["user_id"], poll["tier"], poll.get("display_name") or poll["user_id"],
        )
        if token:
            response.set_cookie(AUTH_COOKIE, token, httponly=True, samesite="lax", max_age=_auth.SESSION_TTL_SECS)
            ip = request.client.host if request.client else "unknown"
            _auth.record_login(
                poll["user_id"], poll.get("display_name") or poll["user_id"], poll["tier"], "sso", ip,
            )
    return response


@app.get("/api/auth/logout")
async def api_logout(response: Response):
    response.delete_cookie(AUTH_COOKIE)
    return RedirectResponse("/login", status_code=302)


@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    user = getattr(request.state, "user", {})
    if user.get("tier") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    rows = _auth.get_active_sessions()
    approved = _auth.get_all_approved_users()
    rows_html = "".join(
        "<tr>"
        f"<td>{html.escape(row.get('user_id', ''))}</td>"
        f"<td>{html.escape(row.get('display_name', ''))}</td>"
        f"<td>{html.escape(row.get('tier', ''))}</td>"
        f"<td>{html.escape(row.get('auth_method', ''))}</td>"
        f"<td>{html.escape(row.get('ip_address', ''))}</td>"
        f"<td>{html.escape(row.get('login_time', ''))}</td>"
        "</tr>"
        for row in rows
    )
    approved_html = "".join(
        "<tr>"
        f"<td>{html.escape(row.get('user_id', ''))}</td>"
        f"<td>{html.escape(row.get('display_name', ''))}</td>"
        f"<td>{html.escape(row.get('tier', ''))}</td>"
        f"<td>{html.escape(row.get('auth_method', ''))}</td>"
        f"<td>{html.escape(row.get('last_seen', ''))}</td>"
        "</tr>"
        for row in approved
    )
    return HTMLResponse(f"""<!doctype html><html><head><title>{html.escape(APP_TITLE)} Admin</title></head><body>
    <h1>{html.escape(APP_TITLE)} Admin</h1>
    <h2>Active Sessions</h2><table>{rows_html or '<tr><td>No active sessions</td></tr>'}</table>
    <h2>Approved Users</h2><table>{approved_html or '<tr><td>No approved users</td></tr>'}</table>
    </body></html>""")


@app.post("/api/chat", response_model=PromptResponse)
async def chat(request: Request, response: Response, body: PromptRequest):
    user_message = body.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session = await _get_or_create(request, response, model=body.model)
    async with session.lock:
        text = await session.send(user_message)

    return PromptResponse(
        response=text,
        timestamp=datetime.now().isoformat(),
        session_id=session.session_id,
        model=session.model,
    )


@app.delete("/api/session")
async def end_session(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE)
    async with _sessions_lock:
        session = _sessions.pop(session_id, None)
    if session:
        await session.cleanup()
    response.delete_cookie(SESSION_COOKIE)
    return {"message": "Session ended"}


@app.post("/api/warmup")
async def warmup(request: Request, response: Response, body: WarmupRequest = WarmupRequest()):
    session = await _get_or_create(request, response, model=body.model)
    if session.startup_phase in ("starting", "warming", "ready"):
        return session.status_dict()

    async def _bg_start() -> None:
        async with session.lock:
            if not session._started or not session._alive():
                try:
                    await session._teardown()
                    session._queue = asyncio.Queue()
                    await session._start()
                except Exception as exc:
                    session.startup_phase = "failed"
                    session.startup_error = str(exc)
                    log.error("[warmup] session=%s startup failed: %s", session.session_id, exc)

    asyncio.ensure_future(_bg_start())
    return session.status_dict()


@app.get("/api/status")
async def status(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)
    async with _sessions_lock:
        session = _sessions.get(session_id)
    if not session:
        return {"startup_phase": "idle", "elapsed_seconds": None, "ready": False, "startup_error": None}
    return session.status_dict()


@app.get("/health")
async def health():
    active = len(_sessions)
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "sessions": {"max": MAX_SESSIONS, "active": active, "free": MAX_SESSIONS - active},
        "auth": {"sso_configured": _auth.sso_configured()},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))