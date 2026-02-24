#!/bin/bash
set -e

echo "=== CenoV2 Installer ==="

# Dependencies
echo "[1/4] Installing dependencies..."
sudo dnf install python3-tkinter python3-pip -y

# PyInstaller
echo "[2/4] Installing PyInstaller..."
pip install pyinstaller --break-system-packages

# Build
echo "[3/4] Building..."
pyinstaller --onefile --noconsole game.py

# Install
echo "[4/4] Installing..."
sudo cp dist/game /usr/local/bin/cenov2

cat > /tmp/cenov2.desktop << EOF
[Desktop Entry]
Name=CenoV2
GenericName=Power Management
Comment=Switch power profiles
Exec=/usr/local/bin/cenov2
Icon=battery
Terminal=false
Type=Application
Categories=System;Settings;HardwareSettings;
Keywords=power;battery;performance;cpu;profile;
EOF

sudo cp /tmp/cenov2.desktop /usr/share/applications/
sudo update-desktop-database

# Cleanup
rm -rf dist build __pycache__ game.spec /tmp/cenov2.desktop

echo ""
echo "Done! Search 'CenoV2' in your app launcher."
