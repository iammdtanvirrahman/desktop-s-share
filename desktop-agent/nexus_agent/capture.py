"""X11 screen capture exposed as a WebRTC video track."""
from __future__ import annotations

from aiortc import VideoStreamTrack
from av import VideoFrame
import mss
from PIL import Image


class DesktopVideoTrack(VideoStreamTrack):
    def __init__(self, max_width: int = 1600, max_height: int = 900):
        super().__init__()
        self._sct = mss.mss()
        if len(self._sct.monitors) < 2:
            raise RuntimeError("No active desktop monitor was found.")
        self._monitor = self._sct.monitors[1]
        self.left = int(self._monitor["left"])
        self.top = int(self._monitor["top"])
        self.width = int(self._monitor["width"])
        self.height = int(self._monitor["height"])
        self.max_width = max_width
        self.max_height = max_height

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        shot = self._sct.grab(self._monitor)
        frame_image = Image.frombytes("RGB", shot.size, shot.rgb)
        frame_image.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
        frame = VideoFrame.from_image(frame_image)
        frame.pts = pts
        frame.time_base = time_base
        return frame

    def close(self):
        self._sct.close()
