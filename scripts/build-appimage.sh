#!/bin/bash
#
# Build AppImage for Task Coach
# This script creates a portable AppImage that bundles Python and all dependencies
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
APP_NAME="TaskCoach"
APP_ID="org.taskcoach.TaskCoach"

# Get version from Python module
if [ -z "$VERSION" ]; then
    VERSION=$(python3 -c "from taskcoachlib.meta import data; print(data.version_full)" 2>/dev/null || echo "1.6.1")
fi

echo "======================================"
echo "Building $APP_NAME AppImage v$VERSION"
echo "======================================"

# Directories
BUILD_DIR="$PROJECT_ROOT/build/appimage"
APPDIR="$BUILD_DIR/$APP_NAME.AppDir"
DIST_DIR="$PROJECT_ROOT/dist"
TOOLS_DIR="$PROJECT_ROOT/tools"

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Create AppDir structure
echo "Creating AppDir structure..."
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/metainfo"

# Get Python info
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_FULL_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
PYTHON_PREFIX=$(python3 -c "import sys; print(sys.prefix)")
PYTHON_EXEC=$(which python3)

echo "Python version: $PYTHON_FULL_VERSION"
echo "Python prefix: $PYTHON_PREFIX"

# Bundle Python interpreter
echo "Bundling Python interpreter..."
mkdir -p "$APPDIR/usr/lib/python${PYTHON_VERSION}"

# Copy Python standard library
if [ -d "$PYTHON_PREFIX/lib/python${PYTHON_VERSION}" ]; then
    cp -r "$PYTHON_PREFIX/lib/python${PYTHON_VERSION}"/* "$APPDIR/usr/lib/python${PYTHON_VERSION}/"
fi

# Copy Python binary and create symlinks
cp "$PYTHON_EXEC" "$APPDIR/usr/bin/python3"
ln -sf python3 "$APPDIR/usr/bin/python"

# Copy libpython
LIBPYTHON=$(find "$PYTHON_PREFIX/lib" /usr/lib -name "libpython${PYTHON_VERSION}*.so*" 2>/dev/null | head -1)
if [ -n "$LIBPYTHON" ] && [ -f "$LIBPYTHON" ]; then
    cp -L "$LIBPYTHON" "$APPDIR/usr/lib/"
    # Also copy any symlinks
    LIBPYTHON_DIR=$(dirname "$LIBPYTHON")
    for lib in "$LIBPYTHON_DIR"/libpython${PYTHON_VERSION}*.so*; do
        if [ -f "$lib" ]; then
            cp -L "$lib" "$APPDIR/usr/lib/" 2>/dev/null || true
        fi
    done
fi

# Get site-packages location
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "Site packages: $SITE_PACKAGES"

# Copy installed packages (site-packages)
echo "Bundling Python packages..."
if [ -d "$SITE_PACKAGES" ]; then
    mkdir -p "$APPDIR/usr/lib/python${PYTHON_VERSION}/site-packages"
    cp -r "$SITE_PACKAGES"/* "$APPDIR/usr/lib/python${PYTHON_VERSION}/site-packages/"
fi

# Also copy user site-packages if they exist
USER_SITE=$(python3 -c "import site; print(site.getusersitepackages())" 2>/dev/null || echo "")
if [ -n "$USER_SITE" ] && [ -d "$USER_SITE" ]; then
    cp -r "$USER_SITE"/* "$APPDIR/usr/lib/python${PYTHON_VERSION}/site-packages/" 2>/dev/null || true
fi

# Install Task Coach into the AppDir
echo "Installing Task Coach..."
cd "$PROJECT_ROOT"

# Copy taskcoachlib package
cp -r taskcoachlib "$APPDIR/usr/lib/python${PYTHON_VERSION}/site-packages/"

# Copy main script
cp taskcoach.py "$APPDIR/usr/bin/"
chmod +x "$APPDIR/usr/bin/taskcoach.py"

# Bundle GTK and wxPython dependencies
echo "Bundling shared libraries..."

# Function to copy library and its dependencies
copy_lib_deps() {
    local lib="$1"
    local dest="$APPDIR/usr/lib"

    if [ ! -f "$lib" ]; then
        return
    fi

    cp -n "$lib" "$dest/" 2>/dev/null || true

    # Get dependencies
    ldd "$lib" 2>/dev/null | grep "=> /" | awk '{print $3}' | while read dep; do
        if [ -f "$dep" ]; then
            local basename=$(basename "$dep")
            # Skip system libs that should not be bundled
            case "$basename" in
                libc.so*|libm.so*|libpthread.so*|libdl.so*|librt.so*|ld-linux*|libstdc++.so*)
                    continue
                    ;;
                *)
                    cp -n "$dep" "$dest/" 2>/dev/null || true
                    ;;
            esac
        fi
    done
}

# Find and bundle wxPython native libraries
WX_PATH=$(python3 -c "import wx; import os; print(os.path.dirname(wx.__file__))" 2>/dev/null || echo "")
if [ -n "$WX_PATH" ] && [ -d "$WX_PATH" ]; then
    echo "Found wxPython at: $WX_PATH"
    # Copy wx .so files
    find "$WX_PATH" -name "*.so*" -type f | while read lib; do
        copy_lib_deps "$lib"
    done
fi

# Bundle GTK3 libraries
echo "Bundling GTK3 libraries..."
GTK_LIBS=(
    libgtk-3.so
    libgdk-3.so
    libgdk_pixbuf-2.0.so
    libpango-1.0.so
    libpangocairo-1.0.so
    libcairo.so
    libcairo-gobject.so
    libgio-2.0.so
    libglib-2.0.so
    libgobject-2.0.so
    libatk-1.0.so
    libharfbuzz.so
    libfontconfig.so
    libfreetype.so
    libpng16.so
    libjpeg.so
    libwebkit2gtk-4.0.so
    libjavascriptcoregtk-4.0.so
    libnotify.so
    libSDL2.so
)

for libname in "${GTK_LIBS[@]}"; do
    # Find library in common locations
    for libdir in /usr/lib/x86_64-linux-gnu /usr/lib64 /lib/x86_64-linux-gnu /usr/lib; do
        lib=$(find "$libdir" -name "${libname}*" -type f 2>/dev/null | head -1)
        if [ -n "$lib" ] && [ -f "$lib" ]; then
            copy_lib_deps "$lib"
            break
        fi
    done
done

# Copy additional required libraries for wxPython
echo "Bundling additional libraries..."
ADDITIONAL_LIBS=(
    libX11.so
    libXext.so
    libXrender.so
    libXrandr.so
    libXi.so
    libXcursor.so
    libXcomposite.so
    libXdamage.so
    libXfixes.so
    libxkbcommon.so
    libwayland-client.so
    libwayland-cursor.so
    libwayland-egl.so
    libEGL.so
    libGL.so
    libepoxy.so
    libfribidi.so
    libthai.so
    libdatrie.so
    libgraphite2.so
    libbrotlidec.so
    libbrotlicommon.so
    liblzma.so
    libxml2.so
    libxslt.so
    libsecret-1.so
    libdbus-1.so
)

for libname in "${ADDITIONAL_LIBS[@]}"; do
    for libdir in /usr/lib/x86_64-linux-gnu /usr/lib64 /lib/x86_64-linux-gnu /usr/lib; do
        lib=$(find "$libdir" -name "${libname}*" -type f 2>/dev/null | head -1)
        if [ -n "$lib" ] && [ -f "$lib" ]; then
            cp -n "$lib" "$APPDIR/usr/lib/" 2>/dev/null || true
            break
        fi
    done
done

# Copy GLib schemas
echo "Bundling GLib schemas..."
mkdir -p "$APPDIR/usr/share/glib-2.0/schemas"
if [ -d "/usr/share/glib-2.0/schemas" ]; then
    cp /usr/share/glib-2.0/schemas/gschemas.compiled "$APPDIR/usr/share/glib-2.0/schemas/" 2>/dev/null || true
fi

# Copy GDK-Pixbuf loaders
echo "Bundling GDK-Pixbuf loaders..."
GDK_PIXBUF_DIR=$(pkg-config --variable=gdk_pixbuf_moduledir gdk-pixbuf-2.0 2>/dev/null || echo "/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders")
if [ -d "$GDK_PIXBUF_DIR" ]; then
    mkdir -p "$APPDIR/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders"
    cp "$GDK_PIXBUF_DIR"/*.so "$APPDIR/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders/" 2>/dev/null || true
    # Copy loaders.cache
    LOADERS_CACHE="${GDK_PIXBUF_DIR}/../loaders.cache"
    if [ -f "$LOADERS_CACHE" ]; then
        cp "$LOADERS_CACHE" "$APPDIR/usr/lib/gdk-pixbuf-2.0/2.10.0/" 2>/dev/null || true
    fi
fi

# Copy icons and theme data
echo "Bundling icon theme..."
mkdir -p "$APPDIR/usr/share/icons/hicolor"
# Copy the application icon
if [ -f "$PROJECT_ROOT/icons.in/taskcoach.png" ]; then
    cp "$PROJECT_ROOT/icons.in/taskcoach.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/taskcoach.png"
fi

# Copy Adwaita icon theme basics (for GTK)
if [ -d "/usr/share/icons/Adwaita" ]; then
    mkdir -p "$APPDIR/usr/share/icons/Adwaita"
    cp -r /usr/share/icons/Adwaita/index.theme "$APPDIR/usr/share/icons/Adwaita/" 2>/dev/null || true
    # Copy commonly needed icon sizes
    for size in 16x16 22x22 24x24 32x32 48x48 scalable; do
        if [ -d "/usr/share/icons/Adwaita/$size" ]; then
            mkdir -p "$APPDIR/usr/share/icons/Adwaita/$size"
            cp -r /usr/share/icons/Adwaita/$size"/* "$APPDIR/usr/share/icons/Adwaita/$size/" 2>/dev/null || true
        fi
    done
fi

# Create desktop file
echo "Creating desktop file..."
cat > "$APPDIR/usr/share/applications/taskcoach.desktop" << 'EOF'
[Desktop Entry]
Name=Task Coach
GenericName=Task Manager
Comment=Your friendly task manager
Exec=taskcoach.py %f
Icon=taskcoach
Terminal=false
Type=Application
Categories=Office;Calendar;ProjectManagement;
Keywords=task;todo;reminder;gtd;project;
MimeType=application/x-taskcoach;
StartupNotify=true
StartupWMClass=taskcoach
EOF

# Copy to AppDir root (required by AppImage)
cp "$APPDIR/usr/share/applications/taskcoach.desktop" "$APPDIR/"

# Create AppStream metadata
echo "Creating AppStream metadata..."
cat > "$APPDIR/usr/share/metainfo/$APP_ID.appdata.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>$APP_ID</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0-or-later</project_license>
  <name>Task Coach</name>
  <summary>Your Friendly Task Manager</summary>
  <description>
    <p>Task Coach is an open source todo manager to manage personal tasks and todo lists.
    It supports composite tasks, i.e. tasks within tasks. In addition, Task Coach allows
    you to categorize your tasks, track efforts against a budget per task, and much more.</p>
    <p>Task Coach is available for Windows, Mac OS X, and GNU/Linux.</p>
  </description>
  <launchable type="desktop-id">taskcoach.desktop</launchable>
  <url type="homepage">https://github.com/realcarbonneau/taskcoach</url>
  <url type="bugtracker">https://github.com/realcarbonneau/taskcoach/issues</url>
  <provides>
    <binary>taskcoach.py</binary>
  </provides>
  <releases>
    <release version="$VERSION" date="$(date +%Y-%m-%d)"/>
  </releases>
  <content_rating type="oars-1.1"/>
</component>
EOF

# Create symlinks at AppDir root
ln -sf usr/share/icons/hicolor/256x256/apps/taskcoach.png "$APPDIR/taskcoach.png"
ln -sf taskcoach.png "$APPDIR/.DirIcon"

# Create AppRun script
echo "Creating AppRun script..."
cat > "$APPDIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
# AppRun script for Task Coach AppImage

# Get the directory where this script is located
APPDIR="$(dirname "$(readlink -f "$0")")"

# Set up environment variables
export PATH="$APPDIR/usr/bin:$PATH"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$LD_LIBRARY_PATH"

# Python environment
PYTHON_VERSION=$(ls "$APPDIR/usr/lib" | grep -E "^python3\.[0-9]+$" | head -1)
export PYTHONHOME="$APPDIR/usr"
export PYTHONPATH="$APPDIR/usr/lib/$PYTHON_VERSION/site-packages:$APPDIR/usr/lib/$PYTHON_VERSION"

# GTK/GLib environment
export GDK_PIXBUF_MODULE_FILE="$APPDIR/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache"
export GDK_PIXBUF_MODULEDIR="$APPDIR/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders"
export GSETTINGS_SCHEMA_DIR="$APPDIR/usr/share/glib-2.0/schemas"
export GTK_PATH="$APPDIR/usr/lib/gtk-3.0"
export GTK_DATA_PREFIX="$APPDIR/usr"
export GTK_THEME="${GTK_THEME:-Adwaita}"

# Icon and theme paths
export XDG_DATA_DIRS="$APPDIR/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# wxPython specific
export WXSUPPRESS_SIZER_FLAGS_CHECK=1

# Handle AppImage-specific arguments
if [ "$1" = "--version" ] || [ "$1" = "-V" ]; then
    exec "$APPDIR/usr/bin/python3" -c "from taskcoachlib.meta import data; print(f'Task Coach {data.version_full}')"
    exit 0
fi

# Run Task Coach
exec "$APPDIR/usr/bin/python3" "$APPDIR/usr/bin/taskcoach.py" "$@"
APPRUN_EOF

chmod +x "$APPDIR/AppRun"

# Update GDK-Pixbuf loader cache to use relative paths
if [ -f "$APPDIR/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache" ]; then
    echo "Updating GDK-Pixbuf loader cache..."
    sed -i "s|/usr/lib|./usr/lib|g" "$APPDIR/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache"
fi

# Remove unnecessary files to reduce size
echo "Cleaning up unnecessary files..."
find "$APPDIR" -name "*.pyc" -delete
find "$APPDIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$APPDIR" -name "*.pyo" -delete
find "$APPDIR" -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
find "$APPDIR" -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/$PYTHON_VERSION/test"
rm -rf "$APPDIR/usr/lib/$PYTHON_VERSION/unittest"
rm -rf "$APPDIR/usr/lib/$PYTHON_VERSION/tkinter"
rm -rf "$APPDIR/usr/lib/$PYTHON_VERSION/idlelib"
rm -rf "$APPDIR/usr/lib/$PYTHON_VERSION/turtledemo"
rm -rf "$APPDIR/usr/lib/$PYTHON_VERSION/ensurepip"

# Strip binaries to reduce size (optional)
echo "Stripping binaries..."
find "$APPDIR" -type f -executable -exec strip --strip-unneeded {} \; 2>/dev/null || true
find "$APPDIR" -name "*.so*" -type f -exec strip --strip-unneeded {} \; 2>/dev/null || true

# Create AppImage
echo "Creating AppImage..."
ARCH="x86_64"
APPIMAGE_NAME="${APP_NAME}-${VERSION}-${ARCH}.AppImage"

cd "$BUILD_DIR"

# Use appimagetool to create the AppImage
if [ -f "$TOOLS_DIR/appimagetool-x86_64.AppImage" ]; then
    APPIMAGETOOL="$TOOLS_DIR/appimagetool-x86_64.AppImage"
elif command -v appimagetool &> /dev/null; then
    APPIMAGETOOL="appimagetool"
else
    echo "Error: appimagetool not found!"
    exit 1
fi

# Extract appimagetool if running in CI (no FUSE)
if [ -n "$CI" ] || [ ! -c /dev/fuse ]; then
    echo "Extracting appimagetool (no FUSE available)..."
    "$APPIMAGETOOL" --appimage-extract 2>/dev/null || true
    APPIMAGETOOL="./squashfs-root/AppRun"
fi

ARCH=$ARCH "$APPIMAGETOOL" "$APPDIR" "$DIST_DIR/$APPIMAGE_NAME"

# Create checksum
echo "Creating checksum..."
cd "$DIST_DIR"
sha256sum "$APPIMAGE_NAME" > "${APPIMAGE_NAME}.sha256"

# Print summary
echo ""
echo "======================================"
echo "AppImage build complete!"
echo "======================================"
echo "Output: $DIST_DIR/$APPIMAGE_NAME"
echo "Size: $(du -h "$DIST_DIR/$APPIMAGE_NAME" | cut -f1)"
echo "SHA256: $(cat "${APPIMAGE_NAME}.sha256")"
echo "======================================"
