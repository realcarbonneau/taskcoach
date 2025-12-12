#!/bin/bash
#
# Local AppImage build script for development/testing
# Run this on a Debian Bookworm or similar system
#
# Prerequisites:
#   sudo apt-get install -y build-essential libgtk-3-dev libglib2.0-dev \
#       fuse libfuse2 patchelf wget python3 python3-pip python3-venv
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Task Coach AppImage Local Builder"
echo "================================="

# Check for required tools
for cmd in python3 pip3 wget patchelf; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed"
        echo "Install with: sudo apt-get install -y python3 python3-pip patchelf wget"
        exit 1
    fi
done

# Create and activate virtual environment
VENV_DIR="$PROJECT_ROOT/build/appimage-venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip wheel setuptools

# Install wxPython - this is the tricky part on Debian
# Try to use a pre-built wheel first
echo "Installing wxPython (this may take a while)..."
pip install wxPython || {
    echo ""
    echo "wxPython pip install failed. On Debian Bookworm, you may need to:"
    echo "  1. Install system wxPython: sudo apt-get install python3-wxgtk4.0"
    echo "  2. Or build from source with extra dependencies:"
    echo "     sudo apt-get install -y libgtk-3-dev libgstreamer1.0-dev \\"
    echo "       libgstreamer-plugins-base1.0-dev libwebkit2gtk-4.0-dev \\"
    echo "       libpng-dev libjpeg-dev libtiff-dev libnotify-dev libsm-dev"
    echo ""
    exit 1
}

# Install Task Coach
echo "Installing Task Coach..."
pip install -e "$PROJECT_ROOT"

# Download tools if not present
TOOLS_DIR="$PROJECT_ROOT/tools"
mkdir -p "$TOOLS_DIR"

if [ ! -f "$TOOLS_DIR/appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q -O "$TOOLS_DIR/appimagetool-x86_64.AppImage" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$TOOLS_DIR/appimagetool-x86_64.AppImage"
fi

# Run the main build script
echo "Building AppImage..."
"$SCRIPT_DIR/build-appimage.sh"

# Deactivate virtual environment
deactivate

echo ""
echo "Build complete! Check dist/ directory for the AppImage."
