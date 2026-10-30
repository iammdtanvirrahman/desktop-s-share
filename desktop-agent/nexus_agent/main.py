"""NEXUS Remote Linux Mint agent — X11 screen streaming MVP."""
from __future__ import annotations

import asyncio
import json
import os
import sys

import websockets
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription

from .capture import DesktopVideoTrack
from .input_control import InputController
from .session import detect_session


def ice_servers() -> list[RTCIceServer]:
    servers = [RTCIceServer(urls=[os.getenv("NEXUS_STUN_URL", "stun:stun.l.google.com:19302")])]
    turn_url = os.getenv("NEXUS_TURN_URL")
    if turn_url:
        username = os.getenv("NEXUS_TURN_USERNAME")
        credential = os.getenv("NEXUS_TURN_CREDENTIAL")
        if not username or not credential:
            raise RuntimeError("TURN URL requires NEXUS_TURN_USERNAME and NEXUS_TURN_CREDENTIAL.")
        servers.append(RTCIceServer(urls=[turn_url], username=username, credential=credential))
    return servers


async def run() -> int:
    session = detect_session()
    print(f"NEXUS Remote desktop session: {session.kind} (DISPLAY={session.display or 'unset'})")
    if not session.supported_for_mvp:
        print("This MVP currently supports X11 only.")
        if session.kind == "wayland":
            print("Wayland screen capture/input must use desktop portals/PipeWire; refusing unsafe fallback.")
        else:
            print('Run from the logged-in desktop session and check: echo "$XDG_SESSION_TYPE"')
        return 2

    signaling_url = os.getenv("NEXUS_SIGNALING_URL", "")
    token = os.getenv("NEXUS_SIGNALING_TOKEN", "")
    room = os.getenv("NEXUS_ROOM", "")
    if not signaling_url.startswith(("wss://", "ws://")) or not token or not room:
        print("Set NEXUS_SIGNALING_URL, NEXUS_SIGNALING_TOKEN, and NEXUS_ROOM.")
        return 2
    if signaling_url.startswith("ws://") and os.getenv("NEXUS_ALLOW_INSECURE_WS") != "1":
        print("Plain ws:// is disabled by default. Use wss://, or explicitly set NEXUS_ALLOW_INSECURE_WS=1 for a trusted local test.")
        return 2

    track = DesktopVideoTrack()
    allow_input = os.getenv("NEXUS_ENABLE_REMOTE_INPUT") == "1"
    controller = InputController(
        track.width, track.height, allowed=allow_input, left=track.left, top=track.top
    )
    pc = RTCPeerConnection(RTCConfiguration(iceServers=ice_servers()))
    pc.addTrack(track)
    print(f"Desktop resolution: {track.width}x{track.height}")
    print("Remote input: locally opted in" if allow_input else "Remote input: DISABLED (set NEXUS_ENABLE_REMOTE_INPUT=1 to opt in locally)")

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("open")
        def on_open():
            channel.send(json.dumps({
                "type": "agent_info",
                "width": track.width,
                "height": track.height,
                "remote_input_allowed": allow_input,
            }))

        @channel.on("close")
        def on_close():
            controller.set_active(False)

        @channel.on("message")
        def on_message(message):
            if not isinstance(message, str):
                return
            try:
                event = json.loads(message)
            except ValueError:
                return
            if not isinstance(event, dict):
                return
            if event.get("type") == "control_request":
                active = bool(allow_input and event.get("enabled"))
                controller.set_active(active)
                channel.send(json.dumps({
                    "type": "control_status",
                    "enabled": active,
                    "reason": "" if allow_input else "Remote input is disabled on the laptop. Start the agent with NEXUS_ENABLE_REMOTE_INPUT=1 to opt in.",
                }))
                return
            controller.handle(message)

    try:
        async with websockets.connect(
            signaling_url, open_timeout=15, ping_interval=20, max_size=1_048_576
        ) as ws:
            await ws.send(json.dumps({"type": "join", "room": room, "role": "agent", "token": token}))
            print(f"Waiting for Android viewer in room '{room}'. Press Ctrl+C to stop.")
            async for raw in ws:
                message = json.loads(raw)
                if not isinstance(message, dict):
                    continue
                if message.get("type") == "error":
                    print("Signaling error:", message.get("message", "unknown"))
                elif message.get("type") == "offer":
                    if pc.remoteDescription is not None:
                        print("Ignoring additional offer; one viewer session is supported.")
                        continue
                    offer = RTCSessionDescription(sdp=message["sdp"], type="offer")
                    await pc.setRemoteDescription(offer)
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)
                    await ws.send(json.dumps({
                        "type": "answer", "room": room, "sdp": pc.localDescription.sdp
                    }))
                    print("WebRTC answer sent; negotiating encrypted media.")
                elif message.get("type") == "peer-ready":
                    print("Viewer connected to signaling; waiting for WebRTC offer.")
    except websockets.ConnectionClosed as exc:
        print(f"Signaling connection closed: {exc}")
    finally:
        controller.set_active(False)
        await pc.close()
        track.close()
    return 0


def main() -> int:
    try:
        return asyncio.run(run())
    except KeyboardInterrupt:
        print("\nNEXUS Remote stopped.")
        return 0
    except Exception as exc:
        print(f"NEXUS Remote error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
