# NEXUS Remote

Android remote viewer + Linux Mint desktop agent. This repository currently contains an early X11 screen-streaming prototype.

## Current milestone: 0.2

- Android app includes a bundled remote-viewer UI.
- Linux agent captures the primary X11 monitor and publishes video over WebRTC.
- FastAPI WebSocket service relays WebRTC offer/answer messages.
- Touch/mouse and keyboard input are disabled by default and require a local opt-in on the laptop.
- Optional TURN configuration is supported by the desktop agent and Android viewer.

**Not production-ready:** no real device-to-device integration test has been completed yet. Internet use requires a publicly reachable signaling server over HTTPS/WSS and a TURN server for networks where direct WebRTC connectivity fails.

## Repository layout

- `android/` — Kotlin Android app and bundled WebRTC viewer.
- `desktop-agent/` — Python Linux Mint agent.
- `signaling/` — authenticated WebSocket signaling relay.
- `docs/` — architecture and setup.

## Linux Mint setup

First check the desktop session:

```bash
echo "$XDG_SESSION_TYPE"
```

This prototype currently supports **X11**. It deliberately exits on Wayland because capture and input must be integrated with the compositor's approved portal/PipeWire APIs.

Install prerequisites:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-tk scrot
```

Install the agent:

```bash
cd desktop-agent
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Run it from the logged-in graphical desktop session. Configure the signaling service first:

```bash
export NEXUS_SIGNALING_URL="wss://YOUR-SERVER/ws"
export NEXUS_SIGNALING_TOKEN="YOUR_LONG_RANDOM_SECRET"
export NEXUS_ROOM="YOUR_PRIVATE_RANDOM_ROOM"
nexus-agent
```

The agent starts in **view-only mode**. To explicitly allow remote mouse/keyboard input on the laptop, stop it and restart with:

```bash
export NEXUS_ENABLE_REMOTE_INPUT=1
nexus-agent
```

Only do this on a device and session you own and intend to control remotely. Keep the desktop session unlocked during testing.

Optional TURN environment variables on the laptop:

```bash
export NEXUS_TURN_URL="turn:YOUR-TURN-HOST:3478?transport=udp"
export NEXUS_TURN_USERNAME="YOUR_TURN_USERNAME"
export NEXUS_TURN_CREDENTIAL="YOUR_TURN_PASSWORD"
```

## Signaling server

On a publicly reachable host with TLS termination in front of Uvicorn:

```bash
cd signaling
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NEXUS_SIGNALING_TOKEN="same-long-random-secret"
uvicorn server:app --host 127.0.0.1 --port 8765
```

Configure your reverse proxy to forward `wss://YOUR-SERVER/ws` to Uvicorn and `/health` to the health endpoint. Do not expose an unauthenticated plain-HTTP signaling service publicly.

The current signaling prototype uses one shared bearer token and in-memory rooms. Before public release, replace this with user/device identity, short-lived pairing codes, per-session authorization, rate limits, abuse protection, and temporary TURN credentials.

## Android build

Open the `android/` directory in Android Studio with JDK 17 and Android SDK 35 installed, then build the `app` debug variant.

With Gradle 8.7 installed:

```bash
gradle -p android assembleDebug
```

APK output:

`android/app/build/outputs/apk/debug/app-debug.apk`

The Android viewer asks for a WSS URL, room, token, and optional TURN URL/credentials. Use the same signaling token and room configured on the laptop. Never put production secrets into source control.

## Security limits

- Screen media uses WebRTC (DTLS-SRTP); signaling must be protected with WSS.
- STUN alone cannot guarantee connectivity across every NAT/firewall. Configure TURN for reliable Internet connections.
- The app does not expose VNC/RDP ports.
- Remote input is disabled by default and requires the laptop owner to start the agent with `NEXUS_ENABLE_REMOTE_INPUT=1`.
- This is an experimental prototype, not a substitute for a security-reviewed remote-support product.
