#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_DIR="$ROOT/desktop-agent"
VENV="$AGENT_DIR/.venv"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/nexus-remote"
CONFIG_FILE="$CONFIG_DIR/agent.env"

if [[ "${XDG_SESSION_TYPE:-unknown}" != "x11" ]]; then
  echo "NEXUS 0.2 currently supports X11 sessions only."
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

cat <<EOF
NEXUS Remote agent installed.

1. Edit your private settings:
   nano "$CONFIG_FILE"

2. Start NEXUS from this logged-in X11 desktop session:
   "$ROOT/scripts/run-agent.sh"

The agent runs in view-only mode by default. To permit remote input,
set NEXUS_ENABLE_REMOTE_INPUT=1 in $CONFIG_FILE, then restart the agent.
Never share your token or TURN credentials.
EOF
