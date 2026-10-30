"""NEXUS Remote Linux Mint desktop agent — initial safe scaffold."""
from __future__ import annotations
import argparse
from .session import detect_session

def main() -> int:
    parser = argparse.ArgumentParser(description="NEXUS Remote Linux desktop agent")
    parser.add_argument("--check", action="store_true", help="check desktop session compatibility")
    args = parser.parse_args()
    session = detect_session()
    print(f"Desktop session: {session.kind}")
    print(f"DISPLAY: {session.display or '(not set)'}")
    if not session.supported_for_mvp:
        print("This build currently supports X11 sessions only.")
        if session.kind == "wayland":
            print("Wayland capture/input portal support is planned; no input will be injected.")
        else:
            print('Run this from the logged-in desktop session; check: echo "$XDG_SESSION_TYPE"')
        return 2
    print("X11 session detected. Agent transport is not configured yet.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
