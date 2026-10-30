#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIGNALING_DIR="$ROOT/signaling"
SIGNALING_VENV="$SIGNALING_DIR/.venv"
PORT="${NEXUS_LOCAL_PORT:-8765}"
LOCAL_IP="${NEXUS_LOCAL_IP:-}"

if [[ -z "$LOCAL_IP" ]]; then
  LOCAL_IP="$(hostname -I | awk '{print $1}')"
fi
if [[ -z "$LOCAL_IP" ]]; then
  echo "Could not detect the laptop LAN IP. Set NEXUS_LOCAL_IP manually." >&2
  exit 2
fi

if [[ ! -x "$SIGNALING_VENV/bin/uvicorn" ]]; then
  python3 -m venv "$SIGNALING_VENV"
  "$SIGNALING_VENV/bin/python" -m pip install --upgrade pip
  "$SIGNALING_VENV/bin/pip" install -r "$SIGNALING_DIR/requirements.txt"
fi

export NEXUS_ALLOW_INSECURE_WS=1
export NEXUS_PAIRING_ADMIN_TOKEN
NEXUS_PAIRING_ADMIN_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(40))')"
mkdir -p "${XDG_CACHE_HOME:-$HOME/.cache}"
export NEXUS_PUBLIC_WSS_URL="ws://$LOCAL_IP:$PORT/ws"
export NEXUS_SIGNALING_URL="$NEXUS_PUBLIC_WSS_URL"
export NEXUS_PAIRING_API_URL="http://$LOCAL_IP:$PORT/api/pairing"

echo "NEXUS Local Wi-Fi mode"
echo "Laptop IP: $LOCAL_IP"
echo "Android and laptop must be on the same trusted Wi-Fi."
echo "Signaling: $NEXUS_PUBLIC_WSS_URL"
echo "Do not expose TCP port $PORT to the Internet."

cd "$SIGNALING_DIR"
"$SIGNALING_VENV/bin/uvicorn" server:app --host 0.0.0.0 --port "$PORT" > "${XDG_CACHE_HOME:-$HOME/.cache}/nexus-signaling.log" 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Signaling server failed. Log: ${XDG_CACHE_HOME:-$HOME/.cache}/nexus-signaling.log" >&2
    exit 1
  fi
  sleep 1
done

cd "$ROOT"
bash "$ROOT/scripts/run-agent.sh"
