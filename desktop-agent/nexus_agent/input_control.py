"""Opt-in X11 input controller. Remote input is disabled by default."""
from __future__ import annotations

import json

KEYS = {
    "enter", "backspace", "tab", "esc", "space", "up", "down", "left", "right",
    "delete", "home", "end", "pageup", "pagedown", "insert",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "shift", "ctrl", "alt", "super",
}


class InputController:
    def __init__(
        self, width: int, height: int, allowed: bool = False, left: int = 0, top: int = 0
    ):
        self.width = width
        self.height = height
        self.left = left
        self.top = top
        self.allowed = allowed
        self.active = False
        self._pyautogui = None
        if allowed:
            import pyautogui
            self._pyautogui = pyautogui
            pyautogui.FAILSAFE = True

    def set_active(self, active: bool) -> None:
        next_active = bool(self.allowed and active)
        if self.active and not next_active:
            self.release_all()
        self.active = next_active

    def release_all(self) -> None:
        if self._pyautogui is None:
            return
        try:
            for button in ("left", "right", "middle"):
                self._pyautogui.mouseUp(button=button)
        except self._pyautogui.FailSafeException:
            pass

    def handle(self, raw: str) -> None:
        if not self.allowed or not self.active or self._pyautogui is None:
            return
        if not isinstance(raw, str) or len(raw) > 4096:
            return
        try:
            event = json.loads(raw)
        except (ValueError, TypeError):
            return
        if not isinstance(event, dict):
            return
        kind = event.get("type")
        p = self._pyautogui
        try:
            if kind in {"move", "down", "up"}:
                x = max(0, min(self.width - 1, int(event.get("x", 0)))) + self.left
                y = max(0, min(self.height - 1, int(event.get("y", 0)))) + self.top
                p.moveTo(x, y, duration=0)
                if kind == "down":
                    p.mouseDown(button=self._button(event.get("button")))
                elif kind == "up":
                    p.mouseUp(button=self._button(event.get("button")))
            elif kind == "click":
                p.click(button=self._button(event.get("button")))
            elif kind == "scroll":
                delta = max(-8, min(8, int(event.get("delta", 0))))
                p.scroll(delta)
            elif kind == "key":
                key = str(event.get("key", "")).lower()
                if len(key) == 1 and key.isascii() and key.isprintable():
                    p.write(key, interval=0)
                elif key in KEYS:
                    p.press(key)
            elif kind == "hotkey":
                keys = event.get("keys")
                if isinstance(keys, list) and 1 <= len(keys) <= 3 and all(str(k).lower() in KEYS for k in keys):
                    p.hotkey(*(str(k).lower() for k in keys))
        except (p.FailSafeException, TypeError, ValueError, OverflowError):
            self.set_active(False)

    @staticmethod
    def _button(value: object) -> str:
        return value if isinstance(value, str) and value in {"left", "right", "middle"} else "left"
