#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/nexus-remote/agent.env"
DESKTOP_APP="$ROOT/desktop-agent/.venv/bin/nexus-desktop"

if [[ ! -x "$DESKTOP_APP" ]]; then
  echo "NEXUS desktop app is not installed. Run scripts/setup-linux-mint.sh first." >&2
  exit 2
fi
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Missing $CONFIG_FILE. Run scripts/setup-linux-mint.sh first." >&2
  exit 2
fi

chmod 600 "$CONFIG_FILE"
set -a
# shellcheck disable=SC1090
source "$CONFIG_FILE"
set +a
exec "$DESKTOP_APP"
