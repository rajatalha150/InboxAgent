#!/bin/bash
set -e

# Build a fully self-contained .deb package for Open Email
# All Python dependencies are bundled — no network needed at install time.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PKG_NAME="open-email"
VERSION="0.1.0"
BUILD_DIR="$SCRIPT_DIR/build/${PKG_NAME}_${VERSION}_all"

echo "=== Building self-contained ${PKG_NAME}_${VERSION}_all.deb ==="

# Clean previous build
rm -rf "$SCRIPT_DIR/build"
mkdir -p "$BUILD_DIR"

# --- Build a venv with all dependencies baked in ---
echo "[1/6] Creating virtual environment and installing dependencies..."
VENV_DIR="$BUILD_DIR/opt/open-email/venv"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install imapclient pyyaml ollama PyQt6 --quiet

# --- Install our application into the venv ---
echo "[2/6] Installing open-email into venv..."
"$VENV_DIR/bin/pip" install "$PROJECT_DIR" --quiet

# --- Make venv relocatable (fix shebangs and paths to /opt/open-email/venv) ---
echo "[3/6] Patching venv paths for target system..."
TARGET_VENV="/opt/open-email/venv"

# Fix shebangs in bin/ scripts
find "$VENV_DIR/bin" -type f -exec grep -l "^#!.*$VENV_DIR" {} \; 2>/dev/null | while read -r f; do
    sed -i "s|$VENV_DIR|$TARGET_VENV|g" "$f"
done

# Fix pyvenv.cfg
sed -i "s|$BUILD_DIR/opt/open-email/venv|$TARGET_VENV|g" "$VENV_DIR/pyvenv.cfg" 2>/dev/null || true

# Fix the activate scripts
for activate in "$VENV_DIR/bin/activate" "$VENV_DIR/bin/activate.csh" "$VENV_DIR/bin/activate.fish"; do
    [ -f "$activate" ] && sed -i "s|$BUILD_DIR/opt/open-email/venv|$TARGET_VENV|g" "$activate"
done

# --- DEBIAN metadata ---
echo "[4/6] Setting up package metadata..."
mkdir -p "$BUILD_DIR/DEBIAN"
cp "$SCRIPT_DIR/debian/control" "$BUILD_DIR/DEBIAN/control"

# Minimal postinst — just config copy, no pip
cat > "$BUILD_DIR/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e
CONFIG_DIR="/etc/open-email"
if [ ! -d "$CONFIG_DIR" ]; then
    mkdir -p "$CONFIG_DIR"
    cp /usr/share/open-email/config/*.yaml "$CONFIG_DIR/" 2>/dev/null || true
fi
echo "Open Email installed successfully."
echo "Run 'open-email --gui' to start the application."
POSTINST

cat > "$BUILD_DIR/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
set -e
if systemctl is-active --quiet open-email 2>/dev/null; then
    systemctl stop open-email
fi
if systemctl is-enabled --quiet open-email 2>/dev/null; then
    systemctl disable open-email
fi
PRERM

chmod 755 "$BUILD_DIR/DEBIAN/postinst" "$BUILD_DIR/DEBIAN/prerm"

# --- CLI entry point ---
echo "[5/6] Creating launcher and desktop entry..."
BIN_DIR="$BUILD_DIR/usr/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/open-email" << 'WRAPPER'
#!/bin/bash
exec /opt/open-email/venv/bin/python -m open_email.main "$@"
WRAPPER
chmod 755 "$BIN_DIR/open-email"

# --- Default config files ---
SHARE_DIR="$BUILD_DIR/usr/share/open-email/config"
mkdir -p "$SHARE_DIR"
cp "$PROJECT_DIR/config/"*.yaml "$SHARE_DIR/"

# --- systemd service ---
SYSTEMD_DIR="$BUILD_DIR/lib/systemd/system"
mkdir -p "$SYSTEMD_DIR"
cp "$SCRIPT_DIR/open-email.service" "$SYSTEMD_DIR/"

# --- Desktop entry ---
APPS_DIR="$BUILD_DIR/usr/share/applications"
mkdir -p "$APPS_DIR"
cat > "$APPS_DIR/open-email.desktop" << 'DESKTOP'
[Desktop Entry]
Name=Open Email
Comment=Privacy-first local AI email organization agent
Exec=open-email --gui
Terminal=false
Type=Application
Categories=Network;Email;Utility;
Keywords=email;organize;ai;
DESKTOP

# --- Build the .deb ---
echo "[6/6] Building .deb package..."
dpkg-deb --build "$BUILD_DIR"

DEB_FILE="$SCRIPT_DIR/build/${PKG_NAME}_${VERSION}_all.deb"
echo ""
echo "=== Build complete ==="
echo "Package: $DEB_FILE"
echo "Size: $(du -h "$DEB_FILE" | cut -f1)"
echo ""
echo "Fully self-contained — no internet required at install time."
echo "Install with:  sudo dpkg -i $DEB_FILE"
echo "Then run:      open-email --gui"
