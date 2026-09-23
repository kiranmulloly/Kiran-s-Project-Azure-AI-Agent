"""Reusable PTY-backed chat session manager.

Each ChatSession owns one long-lived CLI process. The process is started on
the first message, then reused for subsequent messages in the same browser
session so the agent keeps context and avoids repeated cold starts.
"""

from __future__ import annotations

import asyncio
import fcntl
import logging
import os
import pty
import re
import termios
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)

IDLE_TIMEOUT = float(os.getenv("CHAT_UI_IDLE_TIMEOUT", "90"))
FIRST_BYTE_TIMEOUT = float(os.getenv("CHAT_UI_FIRST_BYTE_TIMEOUT", "60"))
PROMPT_DEBOUNCE = float(os.getenv("CHAT_UI_PROMPT_DEBOUNCE", "1"))
STARTUP_TIMEOUT = float(os.getenv("CHAT_UI_STARTUP_TIMEOUT", "900"))
RESPONSE_TIMEOUT = float(os.getenv("CHAT_UI_RESPONSE_TIMEOUT", "600"))

AGENT_COMMAND = os.getenv("CHAT_UI_AGENT_COMMAND", "/app/bin/agent-cli")
AGENT_NAME = os.getenv("CHAT_UI_AGENT_NAME", "web-agent")
AGENT_WORKDIR = os.getenv("CHAT_UI_AGENT_WORKDIR", "/app")
READY_MESSAGE = os.getenv(
    "CHAT_UI_READY_MESSAGE",
    "Reply with one short sentence confirming you are ready.",
)

_SUBPROCESS_ENV = {
    **os.environ,
    "PYTHONUNBUFFERED": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "TERM": "xterm-256color",
}

_ANSI = re.compile(
    r'(?:\x1b(?:[@-Z\\-_]|[78]|\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[()].)'
    r'|[\x80-\x9f]|\x07)',
    re.DOTALL,
)
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_STATUS_BAR_RE = re.compile(
    r'7?\(\s*\S*\s*\)\s*[\U0001F7E0\U0001F7E1\U0001F7E2\U0001F534]?\s*'
    r'[\d.]+k/[\d.]+k\s*tokens\s*\(\d+%\)8?'
)
_TRAILING_PROMPT_RE = re.compile(r'\S*\s*(?:\[[^\[\]]*\]\s*){1,3}\([^()\n]*\)\s*>>>.*\Z', re.DOTALL)
_PROMPT_RE = re.compile(r'>>>\s*$', re.MULTILINE)
_PROMPT_LINE_RE = re.compile(r'^.*>>>\s*$')
_AGENT_RESPONSE_BANNER_RE = re.compile(r'^\s*(?:✓\s*)?AGENT RESPONSE\s*$', re.MULTILINE)
_SKIP_STARTS = ("Agent is loading", "Executing prompt:", "INFO:")


def _build_warmup_msg() -> bytes:
    return (READY_MESSAGE.strip() + "\n").encode()


def _clean(raw: str) -> str:
    text = _ANSI.sub("", raw)
    text = _STATUS_BAR_RE.sub("", text)
    text = _CTRL.sub("", text)
    text = text.replace("\r\n", "\n")
    text = "\n".join(line.split("\r")[-1] for line in text.split("\n"))

    last_match = None
    for match in _AGENT_RESPONSE_BANNER_RE.finditer(text):
        last_match = match
    if last_match:
        text = text[last_match.end():]

    kept = [
        line for line in text.split("\n")
        if line.strip()
        and not line.strip().startswith(_SKIP_STARTS)
        and not _PROMPT_LINE_RE.match(line.strip())
    ]
    result = "\n".join(kept).strip()
    result = _TRAILING_PROMPT_RE.sub("", result).rstrip()
    return result or "(empty response)"


def _has_prompt(raw_tail: bytes) -> bool:
    tail = raw_tail[-512:].decode(errors="replace")
    tail_clean = _CTRL.sub("", _STATUS_BAR_RE.sub("", _ANSI.sub("", tail)))
    return bool(_PROMPT_RE.search(tail_clean))


class ChatSession:
    def __init__(self, session_id: str, model: str = "auto"):
        self.session_id = session_id
        self.model = model or "auto"
        self.last_used = datetime.now()
        self.lock = asyncio.Lock()
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._master_fd: Optional[int] = None
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._started = False
        self._coldstart_via_prompt = False
        self.startup_phase = "idle"
        self.startup_started_at: Optional[datetime] = None
        self.startup_completed_at: Optional[datetime] = None
        self.startup_error: Optional[str] = None

    async def _start(self) -> None:
        log.info("[session=%s] starting agent", self.session_id)
        self.startup_phase = "starting"
        self.startup_started_at = datetime.now()
        self.startup_error = None
        loop = asyncio.get_running_loop()
        self._loop = loop

        master_fd, slave_fd = pty.openpty()
        attrs = termios.tcgetattr(slave_fd)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)

        cmd = [AGENT_COMMAND, "--agent", AGENT_NAME]
        if self.model and self.model != "auto":
            cmd += ["--model", self.model]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=AGENT_WORKDIR,
            env=_SUBPROCESS_ENV,
            close_fds=True,
        )
        os.close(slave_fd)

        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self._proc = proc
        self._master_fd = master_fd
        loop.add_reader(master_fd, self._on_data)

        warmup_bytes = _build_warmup_msg()

        def _send_warmup() -> None:
            self.startup_phase = "warming"
            os.write(self._master_fd, warmup_bytes + b"\r")

        raw = await self._drain(
            STARTUP_TIMEOUT,
            first_byte_timeout=FIRST_BYTE_TIMEOUT,
            detect_prompt=True,
            idle_timeout=IDLE_TIMEOUT,
            on_first_prompt=_send_warmup,
        )
        self._coldstart_via_prompt = _has_prompt(raw)
        self._started = True
        self.startup_phase = "ready"
        self.startup_completed_at = datetime.now()

    def _on_data(self) -> None:
        try:
            data = os.read(self._master_fd, 4096)
            if data:
                self._queue.put_nowait(data)
        except OSError:
            pass

    async def _drain(
        self,
        max_timeout: float,
        first_byte_timeout: float = IDLE_TIMEOUT,
        detect_prompt: bool = True,
        idle_timeout: float = IDLE_TIMEOUT,
        on_first_prompt=None,
    ) -> bytes:
        chunks: list[bytes] = []
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max_timeout

        try:
            first = await asyncio.wait_for(self._queue.get(), timeout=min(first_byte_timeout, deadline - loop.time()))
            chunks.append(first)
        except asyncio.TimeoutError:
            return b""

        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                chunk = await asyncio.wait_for(self._queue.get(), timeout=min(idle_timeout, remaining))
                chunks.append(chunk)
                raw_so_far = b"".join(chunks)
                if detect_prompt and _has_prompt(raw_so_far):
                    if on_first_prompt is not None:
                        on_first_prompt()
                        on_first_prompt = None
                    else:
                        try:
                            chunks.append(await asyncio.wait_for(self._queue.get(), timeout=PROMPT_DEBOUNCE))
                            continue
                        except asyncio.TimeoutError:
                            pass
                        break
            except asyncio.TimeoutError:
                break
        return b"".join(chunks)

    def _alive(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def _teardown(self) -> None:
        pid = self._proc.pid if self._proc else None
        if self._loop and self._master_fd is not None:
            try:
                self._loop.remove_reader(self._master_fd)
            except Exception:
                pass
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None
        if self._proc and self._proc.returncode is None:
            self._proc.kill()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=30)
            except asyncio.TimeoutError:
                log.warning("[session=%s] agent PID %s did not exit within 30s", self.session_id, pid)
        self._proc = None
        self._started = False
        self.startup_phase = "idle"
        self.startup_started_at = None
        self.startup_completed_at = None

    async def send(self, message: str) -> str:
        self.last_used = datetime.now()
        if not self._started or not self._alive():
            await self._teardown()
            self._queue = asyncio.Queue()
            try:
                await self._start()
            except Exception as exc:
                self.startup_phase = "failed"
                self.startup_error = str(exc)
                raise

        stale = await self._drain(max_timeout=3, first_byte_timeout=1, detect_prompt=False, idle_timeout=1)
        if stale:
            log.info("[session=%s] discarded %d stale bytes", self.session_id, len(stale))

        os.write(self._master_fd, (message + "\r").encode())
        raw = await self._drain(RESPONSE_TIMEOUT, first_byte_timeout=FIRST_BYTE_TIMEOUT)
        if not raw and not self._alive():
            return "Agent process exited unexpectedly."
        return _clean(raw.decode(errors="replace"))

    async def cleanup(self) -> None:
        await self._teardown()

    def status_dict(self) -> dict:
        elapsed: Optional[float] = None
        if self.startup_started_at:
            end = self.startup_completed_at or datetime.now()
            elapsed = (end - self.startup_started_at).total_seconds()
        return {
            "session_id": self.session_id,
            "startup_phase": self.startup_phase,
            "elapsed_seconds": round(elapsed, 1) if elapsed is not None else None,
            "startup_error": self.startup_error,
            "ready": self.startup_phase == "ready",
            "model": self.model,
        }