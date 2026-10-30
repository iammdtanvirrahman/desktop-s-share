# NEXUS Remote

Cross-platform remote desktop: Android client + Linux Mint desktop agent.

## Project status
Initial scaffold. Not production-ready; Internet deployment requires HTTPS/WSS, authenticated signaling, and TURN configuration.

## Structure
- android/ — Kotlin Android client
- desktop-agent/ — Linux Mint Python agent (X11 MVP; Wayland portal support planned)
- signaling/ — authenticated WebSocket signaling service
- docs/ — architecture and development notes

## Security
Never expose VNC/RDP or an unauthenticated agent directly to the Internet. Use TLS, strong pairing credentials, short-lived session authorization, TURN credentials, and explicit consent for remote input.

## Roadmap
1. Linux session detection and local agent.
2. WebRTC screen streaming.
3. Touch, mouse and keyboard input.
4. Secure pairing and Internet connectivity with TURN.
5. Android packaging and automated tests.
