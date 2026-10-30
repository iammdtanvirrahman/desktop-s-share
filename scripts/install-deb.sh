#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
chmod +x "$ROOT/scripts/build-deb.sh"
bash "$ROOT/scripts/build-deb.sh" "${1:-0.3.1}"
sudo apt install "$ROOT"/dist/nexus-remote-*.deb
