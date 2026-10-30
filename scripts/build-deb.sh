#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-0.3.1}"
ARCH="$(dpkg --print-architecture)"
PKG="$ROOT/build/nexus-remote-deb"
OUT="$ROOT/dist"
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" "$PKG/opt/nexus-remote" "$PKG/usr/bin" "$PKG/usr/share/applications" "$OUT"
cp -a "$ROOT/desktop-agent" "$ROOT/signaling" "$ROOT/scripts" "$PKG/opt/nexus-remote/"
rm -rf "$PKG/opt/nexus-remote/desktop-agent/.venv" "$PKG/opt/nexus-remote/signaling/.venv"
cat > "$PKG/DEBIAN/control" <<EOF
Package: nexus-remote
Version: $VERSION
Section: net
Priority: optional
Architecture: $ARCH
Depends: python3 (>= 3.10), python3-venv, python3-tk, python3-pip, curl
Maintainer: NEXUS Remote
Description: QR-paired Android remote desktop for Linux
 NEXUS Remote desktop pairing app and local Wi-Fi signaling service.
EOF
cat > "$PKG/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
ROOT=/opt/nexus-remote
python3 -m venv "$ROOT/desktop-agent/.venv"
"$ROOT/desktop-agent/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/desktop-agent/.venv/bin/pip" install "$ROOT/desktop-agent"
python3 -m venv "$ROOT/signaling/.venv"
"$ROOT/signaling/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/signaling/.venv/bin/pip" install -r "$ROOT/signaling/requirements.txt"
mkdir -p /etc/nexus-remote
chmod 700 /etc/nexus-remote
exit 0
EOF
chmod 755 "$PKG/DEBIAN/postinst"
cat > "$PKG/usr/bin/nexus-remote" <<'EOF'
#!/bin/sh
exec bash /opt/nexus-remote/scripts/run-local-wifi.sh "$@"
EOF
chmod 755 "$PKG/usr/bin/nexus-remote"
cat > "$PKG/usr/share/applications/nexus-remote.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=NEXUS Remote
GenericName=Remote Desktop Pairing
Comment=Show a QR code to pair your Android phone
Exec=/usr/bin/nexus-remote
Icon=computer
Terminal=true
Categories=Network;RemoteAccess;
EOF
dpkg-deb --root-owner-group --build "$PKG" "$OUT/nexus-remote-$VERSION-$ARCH.deb"
echo "Built: $OUT/nexus-remote-$VERSION-$ARCH.deb"
