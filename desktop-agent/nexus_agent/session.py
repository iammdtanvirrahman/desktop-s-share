"""Desktop session detection helpers."""
from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class SessionInfo:
    kind: str
    display: str | None
    supported_for_mvp: bool

def detect_session() -> SessionInfo:
    kind = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    return SessionInfo(
        kind=kind,
        display=os.environ.get("DISPLAY"),
        supported_for_mvp=(kind == "x11" and bool(os.environ.get("DISPLAY"))),
    )
