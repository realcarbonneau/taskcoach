#!/bin/bash

# Script to upgrade wxPython to version 4.2.4
# This fixes background coloring issues in Task Coach on Debian Bookworm

set -e

echo "=========================================="
echo "Task Coach - wxPython 4.2.4 Upgrade Script"
echo "=========================================="
echo ""

# Check current wxPython version
echo "Checking current wxPython version..."
CURRENT_VERSION=$(python3 -c "import wx; print(wx.version())" 2>/dev/null || echo "Not installed")
echo "Current version: $CURRENT_VERSION"
echo ""

# Check if we need to upgrade
if echo "$CURRENT_VERSION" | grep -q "4.2.4"; then
    echo "✓ wxPython 4.2.4 is already installed!"
    exit 0
fi

echo "Installing build dependencies..."
echo "This requires sudo privileges."
echo ""

sudo apt-get update
sudo apt-get install -y \
    libgtk-3-dev \
    libnotify-dev \
    libsm-dev \
    libwebkit2gtk-4.0-dev \
    libjpeg-dev \
    libtiff-dev \
    libsdl2-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    build-essential \
    python3-dev

echo ""
echo "Installing wxPython 4.2.4..."
echo "NOTE: This will compile wxPython from source and may take 15-30 minutes."
echo ""

pip3 install --upgrade wxPython==4.2.4

echo ""
echo "=========================================="
echo "Verifying installation..."
echo "=========================================="
NEW_VERSION=$(python3 -c "import wx; print(wx.version())" 2>/dev/null || echo "Failed to import")
echo "New version: $NEW_VERSION"

if echo "$NEW_VERSION" | grep -q "4.2.4"; then
    echo ""
    echo "✓ SUCCESS! wxPython 4.2.4 has been installed."
    echo ""
    echo "Next steps:"
    echo "1. Run Task Coach: python3 taskcoach.py"
    echo "2. Verify version in startup log"
    echo "3. Test background coloring on categories and tasks"
    echo "4. Check that date columns have full-width colored backgrounds"
    echo ""
else
    echo ""
    echo "✗ ERROR: Installation may have failed."
    echo "Please check the error messages above."
    exit 1
fi
