#!/bin/bash
# Build script for TaskCoach AppImage
# This creates a standalone AppImage that includes all dependencies

set -e  # Exit on error
set -x  # Print commands

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
APP_NAME="TaskCoach"
APP_DIR="AppDir"
VERSION=$(python3 -c "from taskcoachlib import meta; print(meta.version)")
ARCH=$(uname -m)
UBUNTU_VERSION="${UBUNTU_VERSION:-ubuntu22.04}"

echo "Building TaskCoach AppImage version $VERSION for $ARCH (${UBUNTU_VERSION})"

# Clean up previous builds
rm -rf "$APP_DIR"
rm -f TaskCoach-*.AppImage

# Create AppDir structure
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR/usr/lib"

# Install Python and dependencies into AppDir
# We'll use the system Python but bundle the dependencies
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python $PYTHON_VERSION"

# Copy application files
echo "Copying application files..."
cp -r taskcoachlib "$APP_DIR/usr/lib/"
cp taskcoach.py "$APP_DIR/usr/lib/"
cp -r icons.in "$APP_DIR/usr/lib/" || true

# Create wrapper script
cat > "$APP_DIR/usr/bin/taskcoach" << 'WRAPPER_EOF'
#!/bin/bash
# TaskCoach AppImage wrapper script

# Get the directory where the AppImage is mounted
APPDIR="${APPDIR:-$(dirname "$(readlink -f "$0")")/../..}"

# Set Python path to include bundled modules
export PYTHONPATH="$APPDIR/usr/lib/python-deps/lib/python*/site-packages:$APPDIR/usr/lib:$PYTHONPATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"

# Run TaskCoach
cd "$APPDIR/usr/lib"
exec python3 taskcoach.py "$@"
WRAPPER_EOF
chmod +x "$APP_DIR/usr/bin/taskcoach"

# Create desktop file
cat > "$APP_DIR/usr/share/applications/taskcoach.desktop" << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Name=Task Coach
GenericName=Task Manager
Comment=Your friendly task manager
Exec=taskcoach
Icon=taskcoach
Categories=Office;ProjectManagement;
Terminal=false
StartupNotify=true
DESKTOP_EOF

# Copy icon
if [ -f "icons.in/taskcoach.png" ]; then
    cp "icons.in/taskcoach.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/taskcoach.png"
    cp "icons.in/taskcoach.png" "$APP_DIR/taskcoach.png"
else
    echo "Warning: Icon file not found"
fi

# Create .DirIcon link
ln -sf usr/share/icons/hicolor/256x256/apps/taskcoach.png "$APP_DIR/.DirIcon" || true

# Copy desktop file to root for AppImage
cp "$APP_DIR/usr/share/applications/taskcoach.desktop" "$APP_DIR/taskcoach.desktop"

# Create AppRun script
cat > "$APP_DIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
# AppRun script for TaskCoach

# Get the directory where the AppImage is mounted
APPDIR="${APPDIR:-$(dirname "$(readlink -f "$0")")}"
export APPDIR

# Run the application
exec "$APPDIR/usr/bin/taskcoach" "$@"
APPRUN_EOF
chmod +x "$APP_DIR/AppRun"

# Install Python dependencies into AppDir
echo "Installing Python dependencies into AppDir..."
mkdir -p "$APP_DIR/usr/lib/python-deps"

# Use pip to install dependencies to a custom location
# Install non-wxPython dependencies first
python3 -m pip install --no-cache-dir --target="$APP_DIR/usr/lib/python-deps" \
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
    || echo "Warning: Some dependencies may have failed to install"

# Install wxPython separately using pre-built wheels (much faster)
echo "Installing wxPython from extras repository..."
python3 -m pip install --no-cache-dir --target="$APP_DIR/usr/lib/python-deps" \
    -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 \
    wxPython \
    || echo "Warning: wxPython installation failed"

# Copy required system libraries that wxPython depends on
echo "Copying required shared libraries..."
mkdir -p "$APP_DIR/usr/lib/x86_64-linux-gnu"

# Find and copy wxPython's shared libraries
if [ -d "$APP_DIR/usr/lib/python-deps/wx" ]; then
    # Copy .so files from wx package
    find "$APP_DIR/usr/lib/python-deps/wx" -name "*.so*" -type f -exec ldd {} \; 2>/dev/null | \
        grep "=>" | awk '{print $3}' | grep -v "^$" | sort -u | while read lib; do
        if [ -f "$lib" ]; then
            libname=$(basename "$lib")
            # Copy important libraries but skip system-critical ones
            if [[ ! "$libname" =~ ^(libc\.|libm\.|libpthread\.|libdl\.|librt\.|libgcc_s\.|libstdc\+\+) ]]; then
                echo "  Copying $libname"
                cp -L "$lib" "$APP_DIR/usr/lib/x86_64-linux-gnu/" 2>/dev/null || true
            fi
        fi
    done
fi

# Update wrapper script to use the bundled Python packages
cat > "$APP_DIR/usr/bin/taskcoach" << 'WRAPPER_EOF2'
#!/bin/bash
# TaskCoach AppImage wrapper script

# Get the directory where the AppImage is mounted
APPDIR="${APPDIR:-$(dirname "$(readlink -f "$0")")/../..}"

# Set Python path to include bundled modules
export PYTHONPATH="$APPDIR/usr/lib/python-deps:$APPDIR/usr/lib:$PYTHONPATH"

# Add bundled libraries to library path (IMPORTANT: put at beginning for priority)
export LD_LIBRARY_PATH="$APPDIR/usr/lib/x86_64-linux-gnu:$APPDIR/usr/lib:$LD_LIBRARY_PATH"

# Ensure GTK and other GUI libraries can be found
export GDK_PIXBUF_MODULEDIR="$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders"
export GDK_PIXBUF_MODULE_FILE="$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders.cache"

# Run TaskCoach
cd "$APPDIR/usr/lib"
exec python3 taskcoach.py "$@"
WRAPPER_EOF2
chmod +x "$APP_DIR/usr/bin/taskcoach"

echo "AppDir structure created successfully"
ls -la "$APP_DIR"

# Download appimagetool if not present
if [ ! -f "appimagetool-${ARCH}.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
    chmod +x "appimagetool-${ARCH}.AppImage"
fi

# Build AppImage
echo "Building AppImage..."
APPIMAGE_NAME="TaskCoach-${VERSION}-${ARCH}-${UBUNTU_VERSION}.AppImage"
ARCH=$ARCH ./appimagetool-${ARCH}.AppImage "$APP_DIR" "$APPIMAGE_NAME"

# Make it executable
chmod +x "$APPIMAGE_NAME"

echo "AppImage built successfully: $APPIMAGE_NAME"
ls -lh TaskCoach-*.AppImage
