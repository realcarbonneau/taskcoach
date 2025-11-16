#!/bin/bash
# Build TaskCoach as an AppImage for maximum Linux compatibility
#
# AppImage bundles ALL dependencies including GLIBC, so it works on
# any Linux distribution from ~2016 onwards.

set -e

echo "=== TaskCoach AppImage Builder ==="
echo ""

# Check if we're on a compatible system
if ! command -v appimagetool &> /dev/null; then
    echo "Installing appimagetool..."
    wget -O appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool
fi

# Create AppDir structure
echo "Creating AppDir structure..."
rm -rf TaskCoach.AppDir
mkdir -p TaskCoach.AppDir/usr/bin
mkdir -p TaskCoach.AppDir/usr/lib
mkdir -p TaskCoach.AppDir/usr/share/applications
mkdir -p TaskCoach.AppDir/usr/share/icons/hicolor/256x256/apps

# Build with PyInstaller first (as a directory, not one-file)
echo "Building with PyInstaller..."
python3.12 -m PyInstaller --clean --onedir --name taskcoach taskcoach.py

# Copy PyInstaller output to AppDir
echo "Copying files to AppDir..."
cp -r dist/taskcoach/* TaskCoach.AppDir/usr/bin/

# Create desktop file
cat > TaskCoach.AppDir/usr/share/applications/taskcoach.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Task Coach
Exec=taskcoach
Icon=taskcoach
Categories=Office;ProjectManagement;
Comment=Your friendly task manager
Terminal=false
EOF

# Copy icon
if [ -f icons.in/taskcoach.png ]; then
    cp icons.in/taskcoach.png TaskCoach.AppDir/usr/share/icons/hicolor/256x256/apps/taskcoach.png
    cp icons.in/taskcoach.png TaskCoach.AppDir/taskcoach.png
else
    echo "Warning: Icon not found, creating placeholder"
    convert -size 256x256 xc:blue TaskCoach.AppDir/taskcoach.png
fi

# Create AppRun script
cat > TaskCoach.AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/taskcoach" "$@"
EOF
chmod +x TaskCoach.AppDir/AppRun

# Create the AppImage
echo "Creating AppImage..."
ARCH=x86_64 ./appimagetool TaskCoach.AppDir TaskCoach-x86_64.AppImage

echo ""
echo "=== Build Complete ==="
echo "AppImage: TaskCoach-x86_64.AppImage"
echo ""
echo "Usage:"
echo "  chmod +x TaskCoach-x86_64.AppImage"
echo "  ./TaskCoach-x86_64.AppImage"
echo ""
echo "This AppImage will work on most Linux distributions from 2016+"
