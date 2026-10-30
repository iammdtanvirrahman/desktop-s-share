"""NEXUS Remote signaling and short-lived QR pairing API.

Run behind HTTPS/WSS. Pairing records are in-memory; use one Uvicorn worker.
"""
from __future__ import annotations

import hmac
import os
import secrets
import time
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect

app = FastAPI(title="NEXUS Remote Signaling")
rooms: dict[str, dict[str, WebSocket]] = {}
pairings: dict[str, dict[str, object]] = {}

PAIRING_TTL_SECONDS = 180
MAX_PAIRINGS = 1000


def _remove_expired_pairings(now: float | None = None) -> None:
    current = time.time() if now is None else now
    expired = [
        room for room, record in pairings.items()
        if float(record["expires_at"]) <= current
    ]
    for room in expired:
        pairings.pop(room, None)


def _new_pairing(ws_url: str, now: float | None = None) -> dict[str, object]:
    current = time.time() if now is None else now
    room = secrets.token_urlsafe(12)
    token = secrets.token_urlsafe(32)
    expires_at = int(current + PAIRING_TTL_SECONDS)
    record: dict[str, object] = {
        "token": token,
        "expires_at": expires_at,
        "active_roles": set(),
    }
    pairings[room] = record
    return {
        "app": "nexus-remote",
        "v": 1,
        "ws_url": ws_url,
        "room": room,
        "token": token,
        "expires_at": expires_at,
    }


@app.get("/health")
async def health():
    return {"service": "nexus-signaling", "status": "ok"}


@app.post("/api/pairing")
async def create_pairing(authorization: str | None = Header(default=None)):
    admin_token = os.environ.get("NEXUS_PAIRING_ADMIN_TOKEN", "")
    public_wss_url = os.environ.get("NEXUS_PUBLIC_WSS_URL", "")
    if not admin_token or not public_wss_url.startswith("wss://"):
        raise HTTPException(status_code=503, detail="Pairing service is not configured")
    expected = f"Bearer {admin_token}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")

    _remove_expired_pairings()
    if len(pairings) >= MAX_PAIRINGS:
        raise HTTPException(status_code=503, detail="Pairing capacity reached; retry shortly")

    payload = _new_pairing(public_wss_url)
    return payload


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    room = role = None
    pairing_record = None
    try:
        hello = await ws.receive_json()
        if not isinstance(hello, dict):
            await ws.close(code=1008)
            return
        room = str(hello.get("room", ""))[:80]
        role = hello.get("role")
        token = str(hello.get("token", ""))
        _remove_expired_pairings()
        pairing_record = pairings.get(room)
        if (
            pairing_record is None
            or float(pairing_record["expires_at"]) <= time.time()
            or not hmac.compare_digest(str(pairing_record["token"]), token)
        ):
            await ws.send_json({"type": "error", "message": "Pairing QR is invalid or expired. Generate a new QR on the laptop."})
            await ws.close(code=1008)
            return
        if role not in {"agent", "viewer"}:
            await ws.close(code=1008)
            return

        active_roles = pairing_record["active_roles"]
        if role in active_roles:
            await ws.send_json({"type": "error", "message": "A device with this role is already connected."})
            await ws.close(code=1008)
            return

        bucket = rooms.setdefault(room, {})
        if role in bucket:
            await ws.send_json({"type": "error", "message": "Role already connected"})
            await ws.close(code=1008)
            return
        active_roles.add(role)
        bucket[role] = ws

        peer = bucket.get("viewer" if role == "agent" else "agent")
        if peer:
            await peer.send_json({"type": "peer-ready"})
            await ws.send_json({"type": "peer-ready"})

        while True:
            message = await ws.receive_json()
            if not isinstance(message, dict) or message.get("type") not in {"offer", "answer", "ice"}:
                continue
            peer = bucket.get("viewer" if role == "agent" else "agent")
            if peer:
                await peer.send_json(message)
    except WebSocketDisconnect:
        pass
    finally:
        if room and role in {"agent", "viewer"}:
            rooms.get(room, {}).pop(role, None)
            if not rooms.get(room):
                rooms.pop(room, None)
            if pairing_record is not None:
                pairing_record["active_roles"].discard(role)
