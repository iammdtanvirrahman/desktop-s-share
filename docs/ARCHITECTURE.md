# NEXUS Remote architecture

## Pairing experience

- Android opens directly into the QR scanner.
- Linux Mint opens a small desktop window and requests a short-lived pairing QR from the signaling server.
- The QR contains a room, a random session token, the WSS URL, and an expiry timestamp.
- The Android app validates the QR and connects automatically; there are no URL, room, or token fields to type.
- QR validity is 3 minutes. Generate a new QR to start a fresh session.
- The desktop window includes a local checkbox for enabling remote input. It is unchecked by default.

## Components
- Android: Kotlin Activity, JourneyApps ZXing scanner, and bundled viewer UI served through AndroidX WebViewAssetLoader.
- Linux Mint desktop UI: Python Tkinter window displaying a QR generated from the pairing response.
- Linux Mint agent: Python process running in the logged-in graphical session.
- Media: WebRTC video track using aiortc and mss screen capture.
- Signaling: FastAPI WebSocket relay for WebRTC offer/answer negotiation.
- Input: WebRTC data channel, handled by PyAutoGUI on X11 only.
- NAT traversal: STUN by default; optional TURN credentials can be included in pairing QR payloads.

## Pairing API

- `POST /api/pairing` requires the server-side admin bearer token.
- The server creates a random room and a 256-bit session token with a 180-second expiry.
- Both the desktop agent and the scanned Android client authenticate with this temporary token.
- Active duplicate agent/viewer roles are rejected.
- Pairing state is in-memory. Run a single Uvicorn worker unless the pairing store is moved to shared storage.

## Current streaming implementation
The desktop agent captures the primary X11 monitor and sends a WebRTC video stream. The Android client creates the data channel and initiates the offer. The signaling server forwards the SDP offer/answer. The prototype waits for ICE gathering to finish before sending SDP rather than trickling ICE candidates.

Remote input is disabled by default. The laptop owner must select the local permission checkbox in the desktop app and the viewer must then press Enable control. The remote input flag is not controlled solely by the phone.

## Display-server compatibility
The first implementation targets X11. Linux Mint installations can run X11 or Wayland. Wayland requires compositor-authorized screen capture and input using desktop portals/PipeWire; this code exits rather than silently falling back to unsupported APIs.

## Internet deployment
A public deployment requires:
1. HTTPS/WSS for signaling.
2. Strong server-only pairing admin token and short-lived per-session QR token.
3. A TURN server with temporary credentials for restrictive NATs.
4. Rate limits, room ownership, session revocation, and abuse protection.
5. Visible session state and a reliable local disconnect control.

No VNC/RDP ports should be exposed directly. The current in-memory signaling service is a development prototype.

## Known limitations
- One viewer and one desktop agent per room.
- Primary monitor only.
- No audio streaming, clipboard sync, file transfer, multi-monitor selection, unattended access, or adaptive bitrate.
- Keyboard text injection is ASCII-only in this prototype.
- The signaling server and TURN infrastructure must be deployed by the operator.
- No end-to-end test between a physical Android phone and Linux Mint laptop is claimed yet.
