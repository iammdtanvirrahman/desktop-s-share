"""Opt-in X11 input controller. Remote input is disabled unless enabled locally."""
from __future__ import annotations

import json
import os

KEYS = {
    "enter", "backspace", "tab", "esc", "space", "up", "down", "left", "right",
    "delete", "home", "end", "pageup", "pagedown", "insert",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "shift", "ctrl", "alt", "super",
}

class InputController:
    def __init__(self, width: int, height: int, enabled: bool):
        self.width = width
        self.height = height
        self.enabled = enabled
        self._pyautogui = None
        if enabled:
            import pyautogui
            self._pyautogui = pyautogui
            pyautogui.FAILSAFE = True

    def handle(self, raw: str) -> None:
        if not self.enabled or self._pyautogui is None:
            return
        if not isinstance(raw, str) or len(raw) > 4096:
            return
        try:
            event = json.loads(raw)
        except (ValueError, TypeError):
            return
        kind = event.get("type")
        p = self._pyautogui
        if kind in {"move", "down", "up"}:
            x = max(0, min(self.width - 1, int(event.get("x", 0))))
            y = max(0, min(self.height - 1, int(event.get("y", 0))))
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

    @staticmethod
    def _button(value: object) -> str:
        return value if value in {"left", "right", "middle"} else "left"
