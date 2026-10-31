"""Real-time paired desk session manager for Sanket Setu (Setu = Bridge).

Allows a Visitor (Signer screen/tablet) and Desk Staff (Counter monitor) to participate
in a synchronized, real-time conversation session across separate devices.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from typing import Any, Literal
import uuid

log = logging.getLogger("sanket_setu.sessions")


@dataclass
class SessionMessage:
    id: str
    role: Literal["visitor", "staff", "system"]
    text_hi: str
    text_en: str
    category: str = "general"  # sign_reading | phrase_board | custom | voice | system
    sign_id: str | None = None
    confidence: float | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeskSession:
    session_id: str
    counter_name: str = "Counter 1"
    operator_name: str = "Help Desk Staff"
    status: str = "active"  # active | closed
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    messages: list[SessionMessage] = field(default_factory=list)
    _subscribers: set = field(default_factory=set, repr=False)

    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "counter_name": self.counter_name,
            "operator_name": self.operator_name,
            "status": self.status,
            "created_at": self.created_at,
            "message_count": len(self.messages),
            "active_connections": len(self._subscribers),
        }


class SessionManager:
    """Thread-safe and async-friendly manager for active desk sessions."""

    def __init__(self):
        self._sessions: dict[str, DeskSession] = {}
        # Create a default counter session so one is always immediately ready to use
        self.create_session("default", counter_name="Main Help Desk", operator_name="Reception")

    def create_session(
        self,
        session_id: str | None = None,
        counter_name: str = "Help Desk 1",
        operator_name: str = "Staff",
    ) -> DeskSession:
        sid = (session_id or f"DESK-{uuid.uuid4().hex[:6].upper()}").strip()
        if sid in self._sessions:
            return self._sessions[sid]
        session = DeskSession(
            session_id=sid,
            counter_name=counter_name.strip() or "Help Desk 1",
            operator_name=operator_name.strip() or "Staff",
        )
        self._sessions[sid] = session
        log.info("Created desk session: %s", sid)
        return session

    def get_session(self, session_id: str) -> DeskSession | None:
        return self._sessions.get(session_id.strip())

    def list_sessions(self) -> list[dict[str, Any]]:
        return [session.summary() for session in self._sessions.values()]

    async def add_message(
        self,
        session_id: str,
        role: Literal["visitor", "staff", "system"],
        text_hi: str,
        text_en: str,
        category: str = "general",
        sign_id: str | None = None,
        confidence: float | None = None,
    ) -> SessionMessage | None:
        session = self.get_session(session_id)
        if not session:
            return None
        msg = SessionMessage(
            id=uuid.uuid4().hex[:8],
            role=role,
            text_hi=text_hi.strip(),
            text_en=text_en.strip(),
            category=category,
            sign_id=sign_id,
            confidence=confidence,
        )
        session.messages.append(msg)
        await self.broadcast(
            session_id,
            {"type": "message", "session_id": session_id, "message": msg.to_dict()},
        )
        return msg

    async def clear_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        session.messages.clear()
        await self.broadcast(
            session_id,
            {"type": "cleared", "session_id": session_id, "message": "Session transcript cleared"},
        )
        return True

    def export_session(self, session_id: str) -> str:
        session = self.get_session(session_id)
        if not session:
            return ""
        lines = [
            f"Sanket Setu · Desk Session Transcript",
            f"Session ID: {session.session_id} | Counter: {session.counter_name}",
            f"Staff: {session.operator_name} | Created: {session.created_at}",
            "=" * 60,
            "",
        ]
        if not session.messages:
            lines.append("No messages recorded in this session.")
        else:
            for m in session.messages:
                tag = "VISITOR" if m.role == "visitor" else ("STAFF" if m.role == "staff" else "SYSTEM")
                lines.append(f"[{m.created_at}] {tag}:")
                if m.text_hi and m.text_en:
                    lines.append(f"  HI: {m.text_hi}")
                    lines.append(f"  EN: {m.text_en}")
                else:
                    lines.append(f"  {m.text_hi or m.text_en}")
                if m.sign_id:
                    lines.append(f"  (Sign: {m.sign_id}, Confidence: {m.confidence or 'N/A'})")
                lines.append("")
        return "\n".join(lines)

    def subscribe(self, session_id: str, websocket) -> None:
        session = self.get_session(session_id)
        if session:
            session._subscribers.add(websocket)
            log.info("WebSocket connected to session %s (total: %d)", session_id, len(session._subscribers))

    def unsubscribe(self, session_id: str, websocket) -> None:
        session = self.get_session(session_id)
        if session and websocket in session._subscribers:
            session._subscribers.remove(websocket)
            log.info("WebSocket disconnected from session %s", session_id)

    async def broadcast(self, session_id: str, payload: dict) -> None:
        session = self.get_session(session_id)
        if not session or not session._subscribers:
            return
        dead = []
        for ws in list(session._subscribers):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in session._subscribers:
                session._subscribers.remove(ws)


# Global singleton instance
session_manager = SessionManager()

