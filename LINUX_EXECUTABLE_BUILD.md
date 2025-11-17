# Linux Executable Build Guide

This document describes how to build standalone Linux executables for TaskCoach using PyInstaller and AppImage.

## Overview

TaskCoach can be distributed as standalone Linux executables in two formats:

1. **PyInstaller** - Creates a directory containing the executable and all dependencies
2. **AppImage** - Creates a single self-contained executable file

Both methods bundle all dependencies including wxPython 4.2.4+, eliminating the need for system-wide installation.

## Prerequisites

### System Dependencies

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
    libjpeg-dev \
    libtiff-dev \
    libpng-dev \
    fuse \
    file \
    wget
```

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
  - `usr/bin/taskcoach`: Wrapper script
  - `usr/lib/`: Application code and bundled dependencies
  - `usr/share/`: Desktop files and icons
- **AppRun**: Entry point script
- **Bundled dependencies**: All Python packages including wxPython 4.2.4+

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

The workflow uploads build artifacts with filenames indicating the build environment:

- **PyInstaller tarball**: `TaskCoach-{version}-{arch}-{ubuntu-version}-pyinstaller.tar.gz`
  - Example: `TaskCoach-1.5.1-x86_64-ubuntu22.04-pyinstaller.tar.gz`
  - Contains the `taskcoach/` directory with executable and all dependencies

- **PyInstaller directory** (for testing): `taskcoach-{version}-{ubuntu-version}-pyinstaller-dir`
  - Unpacked directory artifact for quick testing in CI
  - Retained for 30 days

- **AppImage**: `TaskCoach-{version}-{arch}-{ubuntu-version}.AppImage`
  - Example: `TaskCoach-1.5.1-x86_64-ubuntu22.04.AppImage`
  - Single self-contained executable file

The `{ubuntu-version}` in the filename (e.g., `ubuntu22.04`) indicates:
- **Build environment**: Ubuntu 22.04 (GLIBC 2.35)
- **Minimum requirement**: Requires Ubuntu 22.04+ or equivalent distribution
- **Compatibility**: Works on Debian 12+, RHEL 9+, and most distros from 2022+

Artifacts are retained for 90 days (30 days for directory artifacts).

## wxPython Version

Unlike the Debian package build, these executables use **wxPython 4.2.4+** directly, without the constraints of the Debian Bookworm distribution. This means:

- No patches required for TR_FULL_ROW_HIGHLIGHT or TR_FILL_WHOLE_COLUMN_BACKGROUND
- Latest wxPython features and bug fixes available
- Consistent behavior across different Linux distributions

## GLIBC Compatibility

The executables are built on **Ubuntu 22.04** (GLIBC 2.35) for maximum compatibility with older Linux distributions:

- ✅ **Compatible with**: Ubuntu 22.04+, Debian 12+, RHEL 9+, and most distributions from 2022+
- ⚠️ **Not compatible with**: Ubuntu 20.04 or earlier (GLIBC 2.31), Debian 11 or earlier
- 📦 **Reason**: PyInstaller bundles the Python interpreter and libraries from the build system

If you need to run on older distributions:
1. Use the **AppImage** format (more portable)
2. Or build locally on your target distribution
3. Or use the source installation method

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

## Troubleshooting

### GTK errors

If you see GTK-related errors, ensure all GTK development packages are installed:
```bash
sudo apt-get install libgtk-3-dev
```

### wxPython build failures

If wxPython fails to build from source, try using a pre-built wheel:
```bash
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-24.04 wxPython
```

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

## Version History

- **2025-11**: Initial creation of Linux executable build system
  - PyInstaller support added
  - AppImage support added
  - GitHub Actions workflow created
  - wxPython 4.2.4+ support without Debian constraints
