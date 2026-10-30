# NEXUS Remote

A simple QR-paired remote desktop for Android and Linux Mint.

## The intended experience

**Laptop:** Open NEXUS Remote Desktop. A pairing QR appears automatically.

**Android:** Open NEXUS Remote. The QR scanner opens immediately. Scan the QR on the laptop and the app connects automatically.

No manual IP, room, URL, or token entry is needed.

## Current milestone: 0.3 QR pairing

- Android QR scanner opens on launch (JourneyApps ZXing).
- Linux Mint desktop app automatically requests and displays a 3-minute pairing QR.
- Pairing uses a short-lived random session token; the server admin token never goes into the QR or Android app.
- The laptop app starts the desktop agent and keeps the session alive.
- X11 screen capture streams over WebRTC.
- The laptop's local "Allow this phone to control mouse and keyboard" checkbox is off by default.
- Optional TURN settings can be included in the QR for restrictive networks.

**Not production-ready:** signaling and TURN infrastructure still need to be deployed and configured. An APK build does not mean a physical-device remote session has been tested.

## Repository layout

- `android/` — Kotlin Android QR scanner and remote viewer.
- `desktop-agent/` — Python Linux Mint app and desktop agent.
- `signaling/` — FastAPI pairing API and WebSocket relay.
- `scripts/` — Linux Mint installer and launcher.
- `docs/` — architecture and Android build instructions.

## 1. Deploy the signaling server

Use a public host with HTTPS/WSS reverse proxy. On the server:

```bash
cd signaling
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NEXUS_PUBLIC_WSS_URL="wss://YOUR-SERVER.example/ws"
export NEXUS_PAIRING_ADMIN_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn server:app --host 127.0.0.1 --port 8765 --workers 1
```

Keep the generated admin token private. Configure the reverse proxy to forward:
- `wss://YOUR-SERVER.example/ws` to Uvicorn's `/ws`
- `https://YOUR-SERVER.example/api/pairing` to Uvicorn's `/api/pairing`
- `https://YOUR-SERVER.example/health` to Uvicorn's `/health`

The pairing store is in-memory, so use one Uvicorn worker. For a production multi-worker deployment, move pairing and session state to Redis or another shared store and add rate limiting.

### Optional TURN relay

STUN will not connect every NAT/firewall combination. Configure a TURN server and set its endpoint and short-lived credentials on the signaling server as `NEXUS_TURN_URL`, `NEXUS_TURN_USERNAME`, and `NEXUS_TURN_CREDENTIAL`. The pairing API includes these in the QR payload. Use temporary credentials rather than a permanent public TURN password.

## 2. Install the Linux Mint desktop app

Check the session:

```bash
echo "$XDG_SESSION_TYPE"
```

This milestone supports X11. Wayland portal/PipeWire support is not implemented yet.

### Same-Wi-Fi mode (no VPS / no cloud hosting)

On the laptop, after installing the desktop app, run:

```bash
bash scripts/run-local-wifi.sh
```

This starts the FastAPI signaling service bound to the LAN, creates a fresh random admin token for this run, and opens the desktop pairing window. The script auto-detects the laptop LAN IP; override it with `NEXUS_LOCAL_IP=192.168.0.161` if needed. The phone and laptop must be on the same trusted Wi-Fi. The QR uses unencrypted `ws://` signaling and is intended only for a private LAN; do not expose port 8765 to the Internet. The signaling server and QR token are temporary and local to the laptop. Android accepts `ws://` only for this prototype LAN mode.

Clone and install:

```bash
git clone -b nexus-development https://github.com/iammdtanvirrahman/desktop-s-share.git
cd desktop-s-share
bash scripts/setup-linux-mint.sh
```

Edit the local configuration:

```bash
nano ~/.config/nexus-remote/agent.env
```

Set:
- `NEXUS_SIGNALING_URL=wss://YOUR-SERVER.example/ws`
- `NEXUS_PAIRING_ADMIN_TOKEN=` the same private token generated on the signaling server

Launch:

```bash
bash scripts/run-agent.sh
```

The NEXUS Remote desktop window opens and generates a QR automatically. The QR expires after 3 minutes; press **Generate new QR** to replace it.

The phone can only control mouse/keyboard when the laptop owner checks the local control checkbox before creating the pairing QR. Leave it unchecked for view-only access.

## 3. Install the Android APK

Open the latest successful **NEXUS Remote CI** run for branch `nexus-development` in the repository Actions tab. Download the `nexus-remote-debug-apk` artifact and install `app-debug.apk` from the ZIP.

When Android opens NEXUS Remote, allow camera access and scan the QR displayed on the laptop. The connection starts automatically.

## Security notes

- The server admin token stays on the laptop and signaling server; it is never embedded in Android or the QR.
- QR session tokens are random and expire after 3 minutes.
- WebRTC media uses DTLS-SRTP; use WSS for signaling.
- Remote input is disabled by default and separately enabled on the laptop.
- Do not expose VNC/RDP directly to the Internet.
- This is an experimental prototype and needs a security review before public release.
