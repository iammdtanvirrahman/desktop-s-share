# NEXUS Remote architecture

## Components
- Android: Kotlin Activity with a bundled viewer UI served through AndroidX WebViewAssetLoader.
- Linux Mint agent: Python process running in the logged-in graphical session.
- Media: WebRTC video track using aiortc and mss screen capture.
- Signaling: FastAPI WebSocket relay for WebRTC offer/answer negotiation.
- Input: WebRTC data channel, handled by PyAutoGUI on X11 only.
- NAT traversal: STUN by default; optional TURN credentials on both peers.

## Current implementation
The desktop agent captures the primary monitor and sends a WebRTC video stream. The Android client creates the data channel and initiates the offer. The signaling server forwards the SDP offer/answer. The prototype waits for ICE gathering to finish before sending SDP rather than trickling ICE candidates.

Remote input is disabled on the laptop by default. The laptop owner must explicitly start the process with `NEXUS_ENABLE_REMOTE_INPUT=1`; the viewer then has to request control. Mouse and keyboard input are accepted only after both conditions are met.

## Display-server compatibility
The first implementation targets X11. Linux Mint installations can run X11 or Wayland. Wayland requires compositor-authorized screen capture and input using desktop portals/PipeWire; this code exits rather than silently falling back to unsupported APIs.

## Internet deployment
A public deployment requires:
1. HTTPS/WSS for signaling.
2. Device identity and short-lived pairing authorization rather than one shared static token.
3. A TURN server with temporary credentials for restrictive NATs.
4. Rate limits, room ownership, session revocation, and abuse protection.
5. Visible session state and a reliable local disconnect control.

No VNC/RDP ports should be exposed directly. The current shared-token, in-memory signaling service is development-only.

## Known limitations
- One viewer and one desktop agent per room.
- Primary monitor only.
- No audio streaming, clipboard sync, file transfer, multi-monitor selection, unattended access, or adaptive bitrate.
- Keyboard text injection is ASCII-only in this prototype.
- No successful end-to-end hardware test has yet been recorded.
