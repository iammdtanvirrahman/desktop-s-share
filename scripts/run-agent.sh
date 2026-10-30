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

INHERITED_SIGNALING_URL="${NEXUS_SIGNALING_URL:-}"
INHERITED_PAIRING_TOKEN="${NEXUS_PAIRING_ADMIN_TOKEN:-}"
INHERITED_PAIRING_API_URL="${NEXUS_PAIRING_API_URL:-}"
chmod 600 "$CONFIG_FILE"
set -a
# shellcheck disable=SC1090
source "$CONFIG_FILE"
set +a
# Explicit launcher environment (for example local Wi-Fi mode) takes precedence.
[[ -n "$INHERITED_SIGNALING_URL" ]] && export NEXUS_SIGNALING_URL="$INHERITED_SIGNALING_URL"
[[ -n "$INHERITED_PAIRING_TOKEN" ]] && export NEXUS_PAIRING_ADMIN_TOKEN="$INHERITED_PAIRING_TOKEN"
[[ -n "$INHERITED_PAIRING_API_URL" ]] && export NEXUS_PAIRING_API_URL="$INHERITED_PAIRING_API_URL"
exec "$DESKTOP_APP"
