"""Simple Linux Mint pairing window: show a QR code for the Android app."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import qrcode
import requests
import tkinter as tk
from PIL import ImageTk


class NexusDesktopApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("NEXUS Remote")
        self.root.geometry("390x590")
        self.root.minsize(360, 540)
        self.root.configure(bg="#090b12")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.agent_process: subprocess.Popen | None = None
        self.agent_log = None
        self.qr_photo = None
        self.expires_at = 0
        self.timer_job = None
        self.busy = False

        self.allow_control = tk.BooleanVar(value=False)
        self.title_label = tk.Label(
            self.root, text="NEXUS REMOTE", bg="#090b12", fg="#f4f6ff",
            font=("DejaVu Sans", 18, "bold")
        )
        self.title_label.pack(pady=(28, 4))
        self.subtitle = tk.Label(
            self.root, text="Pair your phone with this computer",
            bg="#090b12", fg="#98a4ba", font=("DejaVu Sans", 10)
        )
        self.subtitle.pack(pady=(0, 18))

        self.qr_panel = tk.Frame(self.root, bg="#ffffff", width=292, height=292)
        self.qr_panel.pack(pady=4)
        self.qr_panel.pack_propagate(False)
        self.qr_label = tk.Label(
            self.qr_panel, text="Preparing secure pairing…",
            bg="#ffffff", fg="#111827", font=("DejaVu Sans", 11)
        )
        self.qr_label.place(relx=0.5, rely=0.5, anchor="center")

        self.status_label = tk.Label(
            self.root, text="Creating a temporary QR code…",
            bg="#090b12", fg="#b8c5dc", font=("DejaVu Sans", 10)
        )
        self.status_label.pack(pady=(18, 4))
        self.timer_label = tk.Label(
            self.root, text="",
            bg="#090b12", fg="#8794a9", font=("DejaVu Sans", 9)
        )
        self.timer_label.pack(pady=(0, 8))

        self.control_check = tk.Checkbutton(
            self.root,
            text="Allow this phone to control mouse and keyboard",
            variable=self.allow_control,
            onvalue=True,
            offvalue=False,
            bg="#090b12",
            fg="#dce5f6",
            activebackground="#090b12",
            activeforeground="#ffffff",
            selectcolor="#1b2536",
            font=("DejaVu Sans", 9),
        )
        self.control_check.pack(pady=(8, 12))

        self.regenerate_button = tk.Button(
            self.root, text="Generate new QR",
            command=self.generate_pairing,
            bg="#dce5ff", fg="#111827", activebackground="#c7d5ff",
            relief="flat", font=("DejaVu Sans", 10, "bold"),
            padx=18, pady=10
        )
        self.regenerate_button.pack()
        self.footer = tk.Label(
            self.root, text="Open NEXUS Remote on Android and scan this QR",
            bg="#090b12", fg="#78869d", font=("DejaVu Sans", 8)
        )
        self.footer.pack(side="bottom", pady=18)

        self.root.after(250, self.generate_pairing)

    def set_status(self, message: str, color: str = "#b8c5dc") -> None:
        self.status_label.configure(text=message, fg=color)

    @staticmethod
    def pairing_api_url(ws_url: str) -> str:
        explicit = os.getenv("NEXUS_PAIRING_API_URL")
        if explicit:
            return explicit
        parts = urlsplit(ws_url)
        if parts.scheme not in {"wss", "ws"} or not parts.netloc:
            raise ValueError("NEXUS_SIGNALING_URL must use wss:// or ws:// on your trusted local Wi-Fi.")
        api_scheme = "https" if parts.scheme == "wss" else "http"
        return urlunsplit((api_scheme, parts.netloc, "/api/pairing", "", ""))

    def generate_pairing(self) -> None:
        if self.busy:
            return
        self.busy = True
        self.regenerate_button.configure(state="disabled")
        self.set_status("Creating a secure QR code…")
        self._stop_agent()
        threading.Thread(target=self._request_pairing, daemon=True).start()

    def _request_pairing(self) -> None:
        try:
            ws_url = os.getenv("NEXUS_SIGNALING_URL", "")
            admin_token = os.getenv("NEXUS_PAIRING_ADMIN_TOKEN", "")
            if not ws_url or not admin_token:
                raise RuntimeError(
                    "Configure NEXUS_SIGNALING_URL and NEXUS_PAIRING_ADMIN_TOKEN in agent.env."
                )
            response = requests.post(
                self.pairing_api_url(ws_url),
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=12,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("app") != "nexus-remote" or payload.get("v") != 1:
                raise RuntimeError("Pairing server returned an unsupported QR payload.")
            returned_ws = str(payload.get("ws_url", ""))
            if not returned_ws.startswith(("wss://", "ws://")):
                raise RuntimeError("Pairing server returned an invalid WebSocket URL.")
            if returned_ws.startswith("ws://") and os.getenv("NEXUS_ALLOW_INSECURE_WS") != "1":
                raise RuntimeError("Unencrypted WebSocket is only allowed in explicit local Wi-Fi mode.")
            self.root.after(0, lambda: self._show_pairing(payload))
        except Exception as exc:
            self.root.after(0, lambda message=str(exc): self._pairing_failed(message))

    def _show_pairing(self, payload: dict) -> None:
        try:
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=7,
                border=3,
            )
            qr.add_data(json.dumps(payload, separators=(",", ":")))
            qr.make(fit=True)
            image = qr.make_image(fill_color="#090b12", back_color="white").convert("RGB")
            image.thumbnail((280, 280))
            self.qr_photo = ImageTk.PhotoImage(image)
            self.qr_label.configure(image=self.qr_photo, text="")
            self.expires_at = int(payload["expires_at"])

            agent_env = os.environ.copy()
            agent_env["NEXUS_SIGNALING_URL"] = str(payload["ws_url"])
            agent_env["NEXUS_ROOM"] = str(payload["room"])
            agent_env["NEXUS_SIGNALING_TOKEN"] = str(payload["token"])
            if self.allow_control.get():
                agent_env["NEXUS_ENABLE_REMOTE_INPUT"] = "1"
            else:
                agent_env.pop("NEXUS_ENABLE_REMOTE_INPUT", None)

            config_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "nexus-remote"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.agent_log = open(config_dir / "agent.log", "a", encoding="utf-8")
            self.agent_process = subprocess.Popen(
                [sys.executable, "-m", "nexus_agent.main"],
                env=agent_env,
                stdin=subprocess.DEVNULL,
                stdout=self.agent_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            self.busy = False
            self.regenerate_button.configure(state="normal")
            self.set_status("QR ready — waiting for your phone", "#9be7bb")
            self._update_countdown()
        except Exception as exc:
            self._pairing_failed(str(exc))

    def _pairing_failed(self, message: str) -> None:
        self.busy = False
        self.regenerate_button.configure(state="normal")
        self.qr_label.configure(image="", text="QR unavailable")
        self.qr_photo = None
        self.set_status(message, "#ffaaaa")
        self.timer_label.configure(text="Check the pairing server and agent.env")

    def _update_countdown(self) -> None:
        remaining = self.expires_at - int(time.time())
        if remaining <= 0:
            self.timer_label.configure(text="QR expired — generate a new one")
            self.set_status("Pairing QR expired", "#ffcc88")
            self._stop_agent()
            return
        self.timer_label.configure(text=f"QR expires in {remaining // 60}:{remaining % 60:02d}")
        self.timer_job = self.root.after(1000, self._update_countdown)

    def _stop_agent(self) -> None:
        if self.timer_job:
            try:
                self.root.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None
        if self.agent_process and self.agent_process.poll() is None:
            self.agent_process.terminate()
            try:
                self.agent_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.agent_process.kill()
        self.agent_process = None
        if self.agent_log:
            self.agent_log.close()
            self.agent_log = None

    def close(self) -> None:
        self._stop_agent()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    try:
        NexusDesktopApp().run()
        return 0
    except Exception as exc:
        print(f"Could not start NEXUS Remote desktop app: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
