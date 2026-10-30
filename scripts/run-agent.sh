#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/nexus-remote/agent.env"
AGENT="$ROOT/desktop-agent/.venv/bin/nexus-agent"

if [[ ! -x "$AGENT" ]]; then
  echo "NEXUS agent is not installed. Run scripts/setup-linux-mint.sh first." >&2
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
exec "$AGENT"
