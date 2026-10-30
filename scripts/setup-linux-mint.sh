#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_DIR="$ROOT/desktop-agent"
VENV="$AGENT_DIR/.venv"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/nexus-remote"
CONFIG_FILE="$CONFIG_DIR/agent.env"

if [[ "${XDG_SESSION_TYPE:-unknown}" != "x11" ]]; then
  echo "NEXUS 0.3 currently supports X11 sessions only."
  echo "Detected: ${XDG_SESSION_TYPE:-unknown}"
  echo 'Check with: echo "$XDG_SESSION_TYPE"'
  echo "Wayland portal/PipeWire support is not part of this build."
  exit 2
fi

sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-tk scrot

python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/pip" install -e "$AGENT_DIR"

mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"
if [[ ! -f "$CONFIG_FILE" ]]; then
  install -m 600 "$AGENT_DIR/.env.example" "$CONFIG_FILE"
fi
chmod 600 "$CONFIG_FILE"

APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APP_DIR"
cat > "$APP_DIR/nexus-remote.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NEXUS Remote
Comment=Pair your Android phone with this computer
Exec=/bin/bash -lc "bash '$ROOT/scripts/run-agent.sh'"
Terminal=false
Categories=Network;RemoteAccess;
EOF
chmod 644 "$APP_DIR/nexus-remote.desktop"

cat <<EOF
NEXUS Remote desktop app installed.

1. Configure the private server details:
   nano "$CONFIG_FILE"

   Set NEXUS_SIGNALING_URL and NEXUS_PAIRING_ADMIN_TOKEN.

2. Start the laptop app:
   bash "$ROOT/scripts/run-agent.sh"

A pairing QR will appear automatically. Open NEXUS Remote on Android and scan it.
The QR expires after 3 minutes. Generate a new one when needed.

The laptop starts in view-only mode. You can explicitly allow mouse/keyboard
control using the checkbox in the laptop pairing window.
EOF
