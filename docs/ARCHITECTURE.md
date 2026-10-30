# NEXUS Remote architecture

## Components
- Android client: native Kotlin application.
- Linux desktop agent: Python service running inside the logged-in graphical session.
- Signaling: FastAPI WebSocket relay for WebRTC offer/answer exchange.
- Media/control plane: WebRTC media plus a data channel, with TURN for restrictive NATs.

## Session compatibility
The initial desktop-agent milestone targets X11. Linux Mint systems may run X11 or Wayland. Wayland capture and input must use compositor-approved portals/PipeWire rather than assuming X11 APIs work.

## Internet deployment
A public deployment needs:
1. HTTPS/WSS for signaling and Android client/API endpoints.
2. Authenticated short-lived pairing (not a static shared token embedded in the app).
3. TURN with temporary credentials and rate limits.
4. WebRTC DTLS-SRTP media and authenticated data channels.
5. Explicit user consent, visible active-session indicator, and immediate disconnect.

No VNC/RDP ports should be exposed directly. Avoid unattended access until a secure device trust/revocation model exists.

## Current status
This commit is scaffolding only. No live screen stream, Android pairing, or remote input is claimed as implemented.
