"""Minimal authenticated WebSocket signaling relay.

Run behind HTTPS/WSS. This is a prototype relay, not a complete identity system.
"""
from __future__ import annotations

import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="NEXUS Remote Signaling")
rooms: dict[str, dict[str, WebSocket]] = {}
TOKEN = os.environ.get("NEXUS_SIGNALING_TOKEN", "")


@app.get("/health")
async def health():
    return {"service": "nexus-signaling", "status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    room = role = None
    try:
        hello = await ws.receive_json()
        room = str(hello.get("room", ""))[:80]
        role = hello.get("role")
        if not TOKEN or hello.get("token") != TOKEN:
            await ws.send_json({"type": "error", "message": "Authentication failed"})
            await ws.close(code=1008)
            return
        if not room or role not in {"agent", "viewer"}:
            await ws.close(code=1008)
            return

        bucket = rooms.setdefault(room, {})
        if role in bucket:
            await ws.send_json({"type": "error", "message": "Role already connected"})
            await ws.close(code=1008)
            return
        bucket[role] = ws

        peer = bucket.get("viewer" if role == "agent" else "agent")
        if peer:
            await peer.send_json({"type": "peer-ready"})
            await ws.send_json({"type": "peer-ready"})

        while True:
            message = await ws.receive_json()
            if message.get("type") not in {"offer", "answer", "ice"}:
                continue
            peer = bucket.get("viewer" if role == "agent" else "agent")
            if peer:
                await peer.send_json(message)
    except WebSocketDisconnect:
        pass
    finally:
        if room and role in {"agent", "viewer"}:
            rooms.get(room, {}).pop(role, None)
            if room in rooms and not rooms[room]:
                rooms.pop(room, None)
