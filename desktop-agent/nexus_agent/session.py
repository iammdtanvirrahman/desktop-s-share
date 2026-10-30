"""Desktop session and Wayland portal capability detection."""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionInfo:
    kind: str
    display: str | None
    supported_for_mvp: bool
    screencast_portal: bool = False
    remote_desktop_portal: bool = False
    portal_error: str | None = None


def _portal_interfaces() -> tuple[bool, bool, str | None]:
    """Query the user's desktop portal without installing or changing sessions."""
    busctl = shutil.which("busctl")
    if not busctl:
        return False, False, "busctl is not installed"
    try:
        result = subprocess.run(
            [
                busctl, "--user", "introspect",
                "org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
            ],
            check=False, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, False, str(exc)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or "portal introspection failed"
        return False, False, detail[:300]
    output = result.stdout
    return (
        "org.freedesktop.portal.ScreenCast" in output,
        "org.freedesktop.portal.RemoteDesktop" in output,
        None,
    )


def detect_session() -> SessionInfo:
    kind = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    display = os.environ.get("DISPLAY")
    if kind == "wayland":
        screencast, remote_desktop, error = _portal_interfaces()
        return SessionInfo(
            kind=kind,
            display=display,
            supported_for_mvp=screencast and remote_desktop,
            screencast_portal=screencast,
            remote_desktop_portal=remote_desktop,
            portal_error=error,
        )
    return SessionInfo(
        kind=kind,
        display=display,
        supported_for_mvp=(kind == "x11" and bool(display)),
    )
