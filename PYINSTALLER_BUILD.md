# PyInstaller Linux Build Guide

This document explains how to build a standalone Linux executable for TaskCoach using PyInstaller.

## Requirements

### wxPython Version Requirement

**IMPORTANT:** TaskCoach requires wxPython 4.2.4 or higher. However, for PyInstaller builds, we use wxPython 4.2.1+ from Ubuntu 24.04 system packages because:

1. Building wxPython from source (pip) requires extensive build dependencies and takes a long time
2. System packages provide pre-compiled binaries optimized for the distribution
3. The system wxPython works correctly with PyInstaller when using the system Python

### System Requirements

- **OS**: Ubuntu 24.04 LTS (or compatible)
- **Python**: 3.12 (system python3)
- **wxPython**: 4.2.1+ (from system packages: python3-wxgtk4.0)

## Local Build Instructions

### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-pip \
  python3-wxgtk4.0 \
  libgtk-3-dev \
  xvfb \
  libnotify4 \
  libwebpdemux2 \
  libraqm0
```

### 2. Verify wxPython Installation

```bash
python3 --version
xvfb-run -a python3 -c "import wx; print('wxPython version:', wx.__version__)"
```

Expected output: `wxPython version: 4.2.1` (or higher)

### 3. Install Python Dependencies

```bash
python3 -m pip install --break-system-packages \
  pyinstaller \
  pypubsub \
  desktop3 \
  pyxdg \
  distro \
  lockfile \
  gntp \
  chardet \
  python-dateutil \
  pyparsing \
  lxml \
  keyring \
  numpy \
  six \
  twisted
```

**Note**: The `--break-system-packages` flag is required for Ubuntu 24.04 (PEP 668 compliance).

### 4. Build the Executable

```bash
python3 -m PyInstaller taskcoach.spec
```

This will create:
- `build/` - Temporary build files
- `dist/taskcoach` - The standalone executable (~61MB)

### 5. Test the Executable

```bash
# Test with version flag
xvfb-run -a ./dist/taskcoach --version

# Test with help flag
xvfb-run -a ./dist/taskcoach --help
```

**Note**: `xvfb-run` is used for headless testing. On a system with a display, you can run `./dist/taskcoach` directly.

## PyInstaller Spec File

The `taskcoach.spec` file includes:

### Data Files Collected
- **Icons**: All PNG, ICO, XPM, BMP files from `taskcoachlib/gui/icons/`
- **Help files**: All files from `taskcoachlib/help/`

### Hidden Imports
The spec file explicitly imports:
- **wxPython modules**: wx, wx._core, wx._adv, wx._html, wx._grid, wx._aui, wx._dataview, wx._xml, wx._xrc, wx.lib.agw.hypertreelist, etc.
- **TaskCoach dependencies**: pypubsub, desktop3, twisted, chardet, dateutil, pyparsing, lxml, pyxdg, keyring, numpy, lockfile, gntp, distro
- **TaskCoach modules**: taskcoachlib and all submodules

### Executable Configuration
- **Console**: False (GUI application)
- **UPX compression**: Enabled
- **Single file**: Yes (all dependencies bundled)

## GitHub Actions Workflow

The automated build workflow (`.github/workflows/build-linux.yml`) runs on:
- **Trigger**: Push to main or claude/* branches, pull requests, manual dispatch
- **Platform**: ubuntu-24.04
- **Python**: System python3 (3.12.x)

### Workflow Steps

1. **Install system dependencies** - Install wxPython and GTK libraries
2. **Verify versions** - Check Python and wxPython availability
3. **Install Python packages** - Install PyInstaller and dependencies
4. **Build executable** - Run PyInstaller with taskcoach.spec
5. **Test executable** - Verify it runs with --version flag
6. **Upload artifacts** - Store executable and build info for 30 days

### Artifacts

Each successful build produces:
- **Executable**: `taskcoach-linux-x86_64-{timestamp}`
- **Build Info**: `taskcoach-linux-x86_64-{timestamp}-info` (BUILD_INFO.txt)

## Common Issues

### Issue 1: ModuleNotFoundError: No module named 'wx'

**Cause**: wxPython not accessible to Python environment

**Solution**:
- Use system python3 (not virtualenv or conda)
- Install python3-wxgtk4.0 system package
- Verify with: `python3 -c "import wx"`

### Issue 2: Library libXss.so.1 not found (warning)

**Cause**: Missing X11 screensaver extension library

**Solution**: This is a warning and can be ignored for headless builds. For GUI builds on desktop:
```bash
sudo apt-get install libxss1
```

### Issue 3: PEP 668 externally-managed-environment error

**Cause**: Ubuntu 24.04 prevents pip from modifying system Python

**Solution**: Use `--break-system-packages` flag:
```bash
python3 -m pip install --break-system-packages {package}
```

### Issue 4: Child process died during PyInstaller build

**Cause**: wxPython initialization requires display (even during analysis)

**Solution**: Use xvfb for headless builds:
```bash
xvfb-run -a python3 -m PyInstaller taskcoach.spec
```

## Technical Details

### Why System Python?

We use the system Python 3.12 instead of a virtual environment or setup-python because:

1. **wxPython availability**: System wxPython packages are compiled for system Python
2. **Binary compatibility**: Pre-compiled system packages match system libraries
3. **Build time**: No need to compile wxPython from source
4. **Reliability**: System packages are tested by the distribution

### Package Sizes

- **wxPython**: ~12MB (shared libraries)
- **TaskCoach source**: ~5MB
- **Python dependencies**: ~40MB
- **Final executable**: ~61MB (all bundled)

### wxPython and PyInstaller

PyInstaller bundles wxPython by:
1. Detecting wxPython imports
2. Collecting all wx.* modules and their C extensions (._core.so, ._adv.so, etc.)
3. Including GTK3 shared libraries
4. Bundling icon and resource files

The spec file explicitly lists hidden imports to ensure all necessary wxPython modules are included.

## Development Notes

### Updating the Spec File

When adding new dependencies or data files:

1. Add hidden imports to the `hiddenimports` list
2. Add data collection logic in the data files section
3. Test the build locally before pushing
4. Verify the executable includes all required files

### Testing Changes

```bash
# Clean previous build
rm -rf build dist

# Rebuild
python3 -m PyInstaller taskcoach.spec

# Test
xvfb-run -a ./dist/taskcoach --version
xvfb-run -a ./dist/taskcoach --help
```

## References

- **PyInstaller Documentation**: https://pyinstaller.org/
- **wxPython Phoenix**: https://wxpython.org/
- **TaskCoach Setup Guide**: See DEBIAN_BOOKWORM_SETUP.md
- **wxPython Patch Info**: See CRITICAL_WXPYTHON_PATCH.md

## Version History

- **2025-11-16**: Initial PyInstaller build setup
  - Created taskcoach.spec for Linux builds
  - Added GitHub Actions workflow
  - Tested on Ubuntu 24.04 with Python 3.12 and wxPython 4.2.1
  - Successfully built 61MB standalone executable

---

**Last Updated**: 2025-11-16
**Tested On**: Ubuntu 24.04 LTS, Python 3.12.3, wxPython 4.2.1
