# Linux Executable Build Guide

This document describes how to build standalone Linux executables for TaskCoach using PyInstaller and AppImage.

## Overview

TaskCoach can be distributed as standalone Linux executables in two formats:

1. **PyInstaller** - Creates a directory containing the executable and all dependencies
2. **AppImage** - Creates a single self-contained executable file

Both methods bundle all dependencies including wxPython 4.2.4+, eliminating the need for system-wide installation.

## Prerequisites

### System Dependencies

**IMPORTANT**: wxPython pre-built wheels require the **runtime** SDL2 library (`libsdl2-2.0-0`), not the development package (`libsdl2-dev`).

```bash
sudo apt-get update
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
    libsdl2-2.0-0 \
    libjpeg-dev \
    libtiff-dev \
    libpng-dev \
    fuse \
    file \
    wget
```

**Note**: If building from source (not using pre-built wheels), you would need `libsdl2-dev` instead of `libsdl2-2.0-0`.

### Python Dependencies

```bash
pip3 install --upgrade pip setuptools wheel
pip3 install pyinstaller distro
```

## Building with PyInstaller

### Manual Build

1. Install dependencies:
```bash
pip3 install -r requirements.txt
pip3 install wxPython>=4.2.4
```

2. Run PyInstaller:
```bash
pyinstaller taskcoach.spec
```

3. The executable will be in `dist/taskcoach/taskcoach`

4. Create a distributable tarball:
```bash
cd dist
tar czf TaskCoach-<version>-<arch>-pyinstaller.tar.gz taskcoach/
```

### Using the Build Script

```bash
./build-linux-executable.sh pyinstaller
```

### PyInstaller Configuration

The `taskcoach.spec` file configures the PyInstaller build:

- **Entry point**: `taskcoach.py`
- **Hidden imports**: All taskcoachlib modules, wx, twisted, and other dependencies
- **Data files**: Help files, translations, icons
- **Executable name**: `taskcoach`
- **Console**: Disabled (GUI application)
- **UPX compression**: Enabled

## Building AppImage

### Manual Build

1. Run the AppImage build script:
```bash
./build-appimage.sh
```

2. The AppImage will be created as `TaskCoach-<version>-<arch>.AppImage`

### Using the Build Script

```bash
./build-linux-executable.sh appimage
```

### AppImage Structure

The AppImage contains:

- **AppDir**: Directory with application files
  - `usr/bin/taskcoach`: Wrapper script with environment isolation
  - `usr/lib/taskcoachlib/`: Application Python code
  - `usr/lib/python-deps/`: Bundled Python packages (wxPython, twisted, numpy, etc.)
  - `usr/lib/x86_64-linux-gnu/`: Bundled shared libraries (.so files)
  - `usr/share/`: Desktop files and icons
- **AppRun**: Entry point script
- **Bundled dependencies**:
  - All Python packages including wxPython 4.2.4+
  - Shared libraries: libSDL2, libjpeg, libpng, libtiff, and wxPython dependencies
  - Crypto libraries: pyOpenSSL, cryptography, cffi (to avoid system conflicts)

### Critical AppImage Features

1. **System Package Isolation**: Uses `PYTHONNOUSERSITE=1` and `python3 -s` to prevent mixing system and bundled packages
2. **Library Priority**: Bundled libraries in `LD_LIBRARY_PATH` take precedence over system libraries
3. **Shared Library Bundling**: Automatically detects and copies all wxPython shared library dependencies using `ldd`
4. **No System OpenSSL Conflicts**: Bundles pyOpenSSL and cryptography to avoid version mismatches

## Building Both Formats

To build both PyInstaller and AppImage executables:

```bash
./build-linux-executable.sh both
```

Or simply:
```bash
./build-linux-executable.sh
```

## Automated Builds with GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/build-linux-executables.yml`) that automatically builds both formats on:

- Push to main/master branches
- Push to branches matching `claude/**`
- Pull requests
- Manual workflow dispatch
- Version tags (`v*`)

### Workflow Jobs

1. **build-pyinstaller**: Builds PyInstaller executable
2. **build-appimage**: Builds AppImage
3. **create-release**: Creates GitHub release with both formats (only on version tags)

### Artifacts

The workflow uploads build artifacts with filenames indicating the build environment and commit:

- **PyInstaller tarball**: `TaskCoach-{version}-{arch}-{ubuntu-version}-{commit-sha}-pyinstaller.tar.gz`
  - Example: `TaskCoach-1.5.1-x86_64-ubuntu22.04-d04d2da-pyinstaller.tar.gz`
  - Contains the `taskcoach/` directory with executable and all dependencies

- **PyInstaller directory** (for testing): `taskcoach-{version}-{ubuntu-version}-{commit-sha}-pyinstaller-dir`
  - Example: `taskcoach-1.5.1-ubuntu22.04-d04d2da-pyinstaller-dir`
  - Unpacked directory artifact for quick testing in CI
  - Retained for 30 days

- **AppImage**: `TaskCoach-{version}-{arch}-{ubuntu-version}-{commit-sha}.AppImage`
  - Example: `TaskCoach-1.5.1-x86_64-ubuntu22.04-d04d2da.AppImage`
  - Single self-contained executable file

**Filename Components**:
- `{version}`: Application version (e.g., `1.5.1`)
- `{arch}`: Architecture (e.g., `x86_64`)
- `{ubuntu-version}`: Build environment (e.g., `ubuntu22.04`)
  - Indicates GLIBC version: Ubuntu 22.04 = GLIBC 2.35
  - Minimum requirement for target systems
- `{commit-sha}`: First 7 characters of git commit (e.g., `d04d2da`)
  - Allows verification of which exact build is being tested
  - Essential for debugging and reproducibility

Artifacts are retained for 90 days (30 days for directory artifacts).

## wxPython Version

Unlike the Debian package build, these executables use **wxPython 4.2.4+** directly, without the constraints of the Debian Bookworm distribution. This means:

- No patches required for TR_FULL_ROW_HIGHLIGHT or TR_FILL_WHOLE_COLUMN_BACKGROUND
- Latest wxPython features and bug fixes available
- Consistent behavior across different Linux distributions

## GLIBC Compatibility

The executables are built on **Ubuntu 22.04** (GLIBC 2.35) for balance between compatibility and maintainability.

### ✅ Compatible Systems (2022+)

**Ubuntu/Derivatives**:
- Ubuntu 22.04 LTS, 22.10, 23.04, 23.10, 24.04 LTS
- Linux Mint 21+
- Pop!_OS 22.04+
- Elementary OS 7+

**Debian**:
- Debian 12 Bookworm (GLIBC 2.36)
- Debian 13 Trixie (testing)

**Red Hat/Derivatives**:
- RHEL 9+, Rocky Linux 9, AlmaLinux 9
- Fedora 36+

**Other**:
- Arch Linux, Manjaro (rolling release)
- openSUSE Leap 15.4+, Tumbleweed

### ⚠️ Incompatible Systems (Still Supported by Vendors)

**These LTS releases are still widely used but won't work**:
- ❌ Ubuntu 20.04 LTS (GLIBC 2.31) - supported until April 2025
- ❌ Debian 11 Bullseye (GLIBC 2.31) - supported until 2026
- ❌ RHEL/CentOS 8 (GLIBC 2.28)

### Why GLIBC Matters

- **PyInstaller**: Bundles Python interpreter compiled against build system's GLIBC
- **AppImage**: Still uses system Python, which links to system GLIBC
- **GLIBC is NOT bundled**: Too fundamental to the system
- **Limitation**: Cannot run on systems with older GLIBC than build environment

### Solutions for Older Systems

If you need to run on Ubuntu 20.04 or Debian 11:

1. **Use source installation** (recommended)
   - Follow instructions in `DEBIAN_BOOKWORM_SETUP.md`
   - Works on any Python 3.8+ system

2. **Build locally on target system**
   - Use `build-linux-executable.sh` on your target distribution
   - Produces executables compatible with that system and newer

3. **Build on Ubuntu 20.04** (for maximum compatibility)
   - Would work on Ubuntu 20.04+ (GLIBC 2.31+)
   - Requires more setup (older wxPython wheels, etc.)
   - Not currently automated

## Testing

### PyInstaller Executable

```bash
cd dist/taskcoach
./taskcoach
```

Or with the tarball:
```bash
tar xzf TaskCoach-<version>-<arch>-pyinstaller.tar.gz
cd taskcoach
./taskcoach
```

### AppImage

```bash
chmod +x TaskCoach-<version>-<arch>.AppImage
./TaskCoach-<version>-<arch>.AppImage
```

The AppImage can also be:
- Double-clicked in a file manager
- Integrated with the desktop (some systems)
- Extracted: `./TaskCoach-*.AppImage --appimage-extract`

## Detailed AppImage Build Process

This section documents the exact build process for reproducibility.

### Step-by-Step Build Process

The `build-appimage.sh` script performs these operations:

#### 1. Configuration and Setup
```bash
VERSION=$(python3 -c "from taskcoachlib import meta; print(meta.version)")
ARCH=$(uname -m)
UBUNTU_VERSION="${UBUNTU_VERSION:-ubuntu22.04}"
COMMIT_SHA="${COMMIT_SHA:-dev}"
```

Creates AppDir structure:
```
AppDir/
├── usr/
│   ├── bin/taskcoach          # Wrapper script
│   ├── lib/
│   │   ├── taskcoachlib/      # Application code
│   │   └── python-deps/       # Bundled Python packages
│   ├── lib/x86_64-linux-gnu/  # Bundled shared libraries
│   └── share/
│       ├── applications/      # Desktop file
│       └── icons/            # Application icons
├── AppRun                     # Entry point
└── taskcoach.desktop         # Desktop integration
```

#### 2. Install Python Dependencies

**Non-wxPython dependencies**:
```bash
python3 -m pip install --no-cache-dir --target="$APP_DIR/usr/lib/python-deps" \
    six>=1.16.0 desktop3 pypubsub twisted chardet>=5.2.0 \
    python-dateutil>=2.9.0 pyparsing>=3.1.2 lxml pyxdg \
    keyring numpy lockfile>=0.12.2 gntp>=1.0.3 \
    pyOpenSSL cryptography cffi
```

**Critical**: `pyOpenSSL`, `cryptography`, and `cffi` MUST be bundled to avoid system OpenSSL version conflicts.

**wxPython** (installed separately for speed):
```bash
python3 -m pip install --no-cache-dir --target="$APP_DIR/usr/lib/python-deps" \
    -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 \
    wxPython
```

#### 3. Bundle Shared Libraries

Automatically detect and copy all wxPython dependencies:

```bash
find "$APP_DIR/usr/lib/python-deps/wx" -name "*.so*" -type f -exec ldd {} \; | \
    grep "=>" | awk '{print $3}' | grep -v "^$" | sort -u | while read lib; do
        libname=$(basename "$lib")
        # Skip system-critical libraries (libc, libm, libpthread, etc.)
        if [[ ! "$libname" =~ ^(libc\.|libm\.|libpthread\.|libdl\.|librt\.|libgcc_s\.|libstdc\+\+) ]]; then
            cp -L "$lib" "$APP_DIR/usr/lib/x86_64-linux-gnu/"
        fi
    done
```

This copies:
- `libSDL2-2.0.so.0` (required by wxPython)
- `libjpeg.so.8`, `libpng16.so.16`, `libtiff.so.5` (image formats)
- All other wxPython shared library dependencies

#### 4. Create Wrapper Script

The wrapper script (`usr/bin/taskcoach`) performs critical environment isolation:

```bash
#!/bin/bash
# Get AppImage mount point
APPDIR="${APPDIR:-$(dirname "$(readlink -f "$0")")/../..}"

# CRITICAL: Use ONLY bundled packages (no system packages)
export PYTHONPATH="$APPDIR/usr/lib/python-deps:$APPDIR/usr/lib"

# Prioritize bundled libraries
export LD_LIBRARY_PATH="$APPDIR/usr/lib/x86_64-linux-gnu:$APPDIR/usr/lib:$LD_LIBRARY_PATH"

# Disable system site-packages to prevent version conflicts
export PYTHONNOUSERSITE=1

# Run with -s flag to ignore user site-packages
exec python3 -s taskcoach.py "$@"
```

**Why these settings matter**:
- `PYTHONPATH`: Only bundled packages, no appending system paths
- `PYTHONNOUSERSITE=1`: Blocks ~/.local/lib/python*/site-packages
- `python3 -s`: Blocks user site-packages directory
- These prevent mixing bundled pyOpenSSL with system OpenSSL

#### 5. Build AppImage

```bash
APPIMAGE_NAME="TaskCoach-${VERSION}-${ARCH}-${UBUNTU_VERSION}-${COMMIT_SHA}.AppImage"
ARCH=$ARCH ./appimagetool-${ARCH}.AppImage "$APP_DIR" "$APPIMAGE_NAME"
```

Uses `appimagetool` to create the final AppImage from AppDir.

### Critical Fixes Applied

These fixes were essential to make the AppImage work:

1. **SDL2 Runtime Library** (`libsdl2-2.0-0`)
   - Problem: wxPython pre-built wheels need runtime library, not dev package
   - Error: `ImportError: libSDL2-2.0.so.0: cannot open shared object file`
   - Solution: Install `libsdl2-2.0-0` instead of `libsdl2-dev`

2. **OpenSSL Version Conflict**
   - Problem: System pyOpenSSL incompatible with system OpenSSL version
   - Error: `AttributeError: module 'lib' has no attribute 'X509_V_FLAG_NOTIFY_POLICY'`
   - Solution: Bundle pyOpenSSL, cryptography, cffi; isolate from system packages

3. **Shared Library Dependencies**
   - Problem: wxPython .so files depend on system libraries
   - Error: `ImportError: libjpeg.so.8: cannot open shared object file`
   - Solution: Use `ldd` to detect and bundle all dependencies

4. **Package Isolation**
   - Problem: System packages mixing with bundled packages
   - Solution: `PYTHONNOUSERSITE=1` and `python3 -s` flag

### Verification Steps

After building, verify the AppImage:

1. **Test extraction**:
   ```bash
   ./TaskCoach-*.AppImage --appimage-extract
   ```

2. **Check bundled libraries**:
   ```bash
   ls squashfs-root/usr/lib/x86_64-linux-gnu/
   # Should see: libSDL2-2.0.so.0, libjpeg.so.8, libpng*.so, etc.
   ```

3. **Verify Python isolation**:
   ```bash
   grep PYTHONNOUSERSITE squashfs-root/usr/bin/taskcoach
   # Should output: export PYTHONNOUSERSITE=1
   ```

4. **Check dependencies**:
   ```bash
   ls squashfs-root/usr/lib/python-deps/
   # Should include: wx/, twisted/, pyOpenSSL/, cryptography/, etc.
   ```

## Troubleshooting

### GTK errors

If you see GTK-related errors, ensure all GTK development packages are installed:
```bash
sudo apt-get install libgtk-3-dev
```

### SDL2 Library Missing

**Error**: `ImportError: libSDL2-2.0.so.0: cannot open shared object file`

**Solution**: Install the runtime library (not the dev package):
```bash
sudo apt-get install libsdl2-2.0-0
```

**Common mistake**: Installing `libsdl2-dev` instead of `libsdl2-2.0-0`. The dev package contains headers for compiling, not the runtime library.

### wxPython build failures

If wxPython fails to build from source, use pre-built wheels:
```bash
# For Ubuntu 22.04
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython

# For Ubuntu 24.04
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-24.04 wxPython
```

### OpenSSL/Crypto Errors in AppImage

**Error**: `AttributeError: module 'lib' has no attribute 'X509_V_FLAG_NOTIFY_POLICY'`

**Cause**: System pyOpenSSL conflicts with bundled twisted

**Solution**: Ensure the AppImage bundles crypto libraries:
```bash
# Check if bundled
./TaskCoach-*.AppImage --appimage-extract
ls squashfs-root/usr/lib/python-deps/ | grep -E "(pyOpenSSL|cryptography|cffi)"
```

If missing, rebuild with latest `build-appimage.sh` which includes these in the dependency list.

### AppImage won't run

1. Ensure FUSE is installed: `sudo apt-get install fuse`
2. Make it executable: `chmod +x TaskCoach-*.AppImage`
3. Try extracting and running manually:
   ```bash
   ./TaskCoach-*.AppImage --appimage-extract
   cd squashfs-root
   ./AppRun
   ```

### Missing dependencies in bundled executable

Check the PyInstaller build output for warnings about missing modules. Add any missing imports to the `hiddenimports` list in `taskcoach.spec`.

### AppImage Shared Library Errors

**Error**: `ImportError: lib*.so.*: cannot open shared object file`

**Diagnosis**: The shared library bundling step failed

**Solution**:
1. Ensure `ldd` command is available
2. Check the build log for library copying step
3. Manually verify wxPython installation:
   ```bash
   python3 -c "import wx; print(wx.__file__)"
   ldd /path/to/wx/_core.*.so
   ```

### GLIBC Version Mismatch

**Error**: `/lib/x86_64-linux-gnu/libm.so.6: version 'GLIBC_2.XX' not found`

**Cause**: Executable built on newer system than runtime system

**Solutions**:
1. Download AppImage built on Ubuntu 22.04 (GLIBC 2.35)
2. Build locally on your target system
3. Use source installation instead

## File Descriptions

- **taskcoach.spec**: PyInstaller specification file
- **build-appimage.sh**: AppImage build script
- **build-linux-executable.sh**: Main build script for both formats
- **.github/workflows/build-linux-executables.yml**: GitHub Actions workflow

## Comparison: PyInstaller vs AppImage

| Feature | PyInstaller | AppImage |
|---------|-------------|----------|
| **Format** | Directory with executable | Single file |
| **Portability** | Requires extraction | Run directly |
| **Size** | Smaller (shared libs) | Larger (all bundled) |
| **Distribution** | Tarball | Single file |
| **Desktop Integration** | Manual | Automatic (some systems) |
| **Dependencies** | Requires GLIBC | Self-contained |

## Best Practices

1. **Test on multiple distributions**: Ubuntu, Debian, Fedora, Arch, etc.
2. **Test different versions**: Test on older distributions to ensure compatibility
3. **Monitor size**: Keep an eye on executable size and optimize if needed
4. **Verify wxPython version**: Ensure wxPython 4.2.4+ is being used
5. **Check for missing files**: Verify all icons, help files, and translations are included

## Related Documentation

- [DEBIAN_BOOKWORM_SETUP.md](DEBIAN_BOOKWORM_SETUP.md) - Debian-specific setup
- [CRITICAL_WXPYTHON_PATCH.md](CRITICAL_WXPYTHON_PATCH.md) - wxPython patch info (not needed for executables)
- [README.md](README.md) - Main project documentation

## Build History and Lessons Learned

### 2025-11-17: Initial Implementation

**Added**:
- PyInstaller specification file (`taskcoach.spec`)
- AppImage build script (`build-appimage.sh`)
- Unified build script (`build-linux-executable.sh`)
- GitHub Actions workflow (`.github/workflows/build-linux-executables.yml`)
- Comprehensive documentation

**Key Decisions**:
- Build on Ubuntu 22.04 (GLIBC 2.35) for reasonable compatibility
- Use wxPython 4.2.4+ pre-built wheels (no Debian patches needed)
- Bundle all dependencies to create self-contained executables
- Add commit SHA to filenames for build verification

**Critical Fixes Applied**:

1. **Dependency Package Confusion** (Resolved: d04d2da)
   - Initial mistake: Installed `libsdl2-dev` (development headers)
   - Actual requirement: `libsdl2-2.0-0` (runtime library)
   - Lesson: Pre-built wheels need runtime libraries, not dev packages

2. **OpenSSL Version Conflicts** (Resolved: d04d2da)
   - Problem: System pyOpenSSL + bundled twisted = version mismatch
   - Solution: Bundle pyOpenSSL, cryptography, cffi in AppImage
   - Isolation: `PYTHONNOUSERSITE=1` and `python3 -s` flag
   - Lesson: Crypto libraries must be bundled or conflicts occur

3. **Shared Library Dependencies** (Resolved: 1e91dd0)
   - Problem: wxPython depends on libjpeg, libpng, libSDL2, etc.
   - Solution: Use `ldd` to detect and bundle all .so dependencies
   - Lesson: Can't assume pre-built wheels are self-contained

4. **Build Environment** (Resolved: 1e91dd0)
   - Initial: Ubuntu 24.04 (GLIBC 2.38)
   - Changed: Ubuntu 22.04 (GLIBC 2.35)
   - Reason: Broader compatibility with existing systems
   - Trade-off: Won't work on Ubuntu 20.04 LTS

5. **Package Conflicts** (Resolved: e3cda7c, 477311e)
   - Tried: GStreamer, freeglut (dependency conflicts)
   - Result: Not needed for wxPython, removed
   - Kept: SDL2 (required by wxPython pre-built wheels)

**Testing Approach**:
- Local testing limited by missing DISPLAY (GUI environment)
- Iterative fixes through GitHub Actions runs
- User testing on actual target systems essential
- Lesson: Should have used Docker for local testing first

**Reproducibility**:
- Commit SHA in filenames enables exact build verification
- Documentation includes all critical fixes and their reasons
- Build scripts are self-contained and version-controlled
