#!/bin/bash
# Main build script for TaskCoach Linux executables
# Supports both PyInstaller and AppImage builds

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
BUILD_TYPE="${1:-both}"  # pyinstaller, appimage, or both

echo "========================================="
echo "TaskCoach Linux Executable Builder"
echo "========================================="
echo "Build type: $BUILD_TYPE"
echo ""

# Function to install dependencies
install_dependencies() {
    echo "Installing dependencies..."

    # Install system dependencies (GTK, etc.)
    if command -v apt-get &> /dev/null; then
        echo "Installing system dependencies via apt-get..."
        sudo apt-get update || true
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-dev \
            libgtk-3-dev \
            libglib2.0-dev \
            libcairo2-dev \
            libpango1.0-dev \
            libatk1.0-dev \
            libgdk-pixbuf2.0-dev \
            libnotify-dev \
            libsdl2-dev \
            libjpeg-dev \
            libtiff-dev \
            libpng-dev \
            freeglut3-dev \
            libgstreamer1.0-dev \
            libgstreamer-plugins-base1.0-dev \
            fuse \
            file \
            wget \
            || echo "Warning: Some system packages failed to install"
    fi

    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip3 install --upgrade pip setuptools wheel || true
    pip3 install pyinstaller || true

    # Install application dependencies
    pip3 install \
        six>=1.16.0 \
        desktop3 \
        pypubsub \
        twisted \
        chardet>=5.2.0 \
        python-dateutil>=2.9.0 \
        pyparsing>=3.1.2 \
        lxml \
        pyxdg \
        keyring \
        numpy \
        lockfile>=0.12.2 \
        gntp>=1.0.3 \
        || echo "Warning: Some Python packages failed to install"

    # Try to install wxPython (may fail if system doesn't have GTK dev files)
    echo "Installing wxPython..."
    pip3 install wxPython>=4.2.4 || \
        pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-24.04 wxPython || \
        echo "Warning: wxPython installation failed. Will try to use system wxPython."

    echo "Dependencies installed (some may have failed, will be handled in CI)"
}

# Function to build with PyInstaller
build_pyinstaller() {
    echo ""
    echo "========================================="
    echo "Building with PyInstaller"
    echo "========================================="

    # Clean previous builds
    rm -rf build dist

    # Run PyInstaller
    if [ -f "taskcoach.spec" ]; then
        pyinstaller taskcoach.spec
    else
        echo "Error: taskcoach.spec not found!"
        exit 1
    fi

    # Check if build succeeded
    if [ -d "dist/taskcoach" ]; then
        echo ""
        echo "PyInstaller build successful!"
        echo "Output directory: dist/taskcoach"
        ls -lh dist/taskcoach/taskcoach

        # Create a tarball
        VERSION=$(python3 -c "from taskcoachlib import meta; print(meta.version)")
        ARCH=$(uname -m)
        cd dist
        tar czf "TaskCoach-${VERSION}-${ARCH}-pyinstaller.tar.gz" taskcoach/
        cd ..
        echo "Created tarball: dist/TaskCoach-${VERSION}-${ARCH}-pyinstaller.tar.gz"
    else
        echo "Error: PyInstaller build failed!"
        exit 1
    fi
}

# Function to build AppImage
build_appimage() {
    echo ""
    echo "========================================="
    echo "Building AppImage"
    echo "========================================="

    if [ -f "build-appimage.sh" ]; then
        ./build-appimage.sh
    else
        echo "Error: build-appimage.sh not found!"
        exit 1
    fi
}

# Main execution
case "$BUILD_TYPE" in
    "deps")
        install_dependencies
        ;;
    "pyinstaller")
        build_pyinstaller
        ;;
    "appimage")
        build_appimage
        ;;
    "both")
        build_pyinstaller
        build_appimage
        ;;
    *)
        echo "Usage: $0 [deps|pyinstaller|appimage|both]"
        echo "  deps        - Install dependencies only"
        echo "  pyinstaller - Build PyInstaller executable only"
        echo "  appimage    - Build AppImage only"
        echo "  both        - Build both (default)"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "Build completed successfully!"
echo "========================================="
