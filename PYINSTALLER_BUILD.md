# TaskCoach PyInstaller Build Guide

This document explains how to build TaskCoach as a standalone executable using PyInstaller for **Windows** and **Linux**.

## Table of Contents

- [Overview](#overview)
- [Windows Build](#windows-build)
- [Linux Build](#linux-build)
- [Common Issues](#common-issues)
- [GitHub Actions](#github-actions)

---

## Overview

PyInstaller packages TaskCoach into a self-contained executable that includes Python, wxPython, and all dependencies. Users can run the application without installing Python.

### Build Workflows

Two GitHub Actions workflows are available:

1. **`.github/workflows/build-windows-exe.yml`** - Windows executable build
2. **`.github/workflows/build-linux-exe.yml`** - Linux executable build

Both workflows:
- Use Python 3.11
- Require wxPython 4.2.4+ (critical for UI fixes)
- Use `--log-level=TRACE` to debug hanging issues
- Upload build artifacts and logs
- Include comprehensive error handling

---

## Windows Build

### Requirements

- **Python**: 3.11 or later
- **wxPython**: 4.2.4 or later (CRITICAL)
- **PyInstaller**: Latest version
- **Platform**: Windows 10/11 or Windows Server 2019+

### Critical: wxPython 4.2.4+

**You MUST use wxPython 4.2.4 or later**. Earlier versions have critical bugs:

- **Issue #2081**: `TR_FULL_ROW_HIGHLIGHT` doesn't draw item backgrounds
- **Issue #1898**: `TR_FILL_WHOLE_COLUMN_BACKGROUND` doesn't fill right-aligned columns

These were fixed in wxPython 4.2.4 via PR #2088. See `CRITICAL_WXPYTHON_PATCH.md` for details.

On Windows, install directly via pip:
```bash
pip install "wxPython>=4.2.4"
```

### Automated Build (GitHub Actions)

The workflow runs automatically when you push to the build branch:

```bash
git push -u origin claude/pyinstaller-windows-build-01Czh7R5Phw5PrbYuG68Wxtp
```

**What it does**:
1. Sets up Windows environment with Python 3.11
2. Installs wxPython 4.2.4+
3. Installs PyInstaller and all dependencies
4. Generates templates and icons
5. Builds with `--log-level=TRACE`
6. Tests executable with `--help` and `--version`
7. Packages as `TaskCoach-Windows-x64.zip`
8. Uploads artifacts (30-day retention)

**Download the build**:
- Go to GitHub Actions tab
- Find the latest workflow run
- Download `TaskCoach-Windows-x64.zip` from artifacts

### Manual Build (Local Windows)

1. **Install Python 3.11**:
   ```cmd
   # Download from https://www.python.org/downloads/
   # Add to PATH during installation
   ```

2. **Install wxPython 4.2.4+**:
   ```cmd
   pip install "wxPython>=4.2.4"
   python -c "import wx; print(wx.version())"
   ```

3. **Install PyInstaller**:
   ```cmd
   pip install pyinstaller
   ```

4. **Install dependencies**:
   ```cmd
   pip install six>=1.16.0 desktop3 pypubsub twisted
   pip install chardet>=5.2.0 python-dateutil>=2.9.0
   pip install pyparsing>=3.1.2 lxml keyring numpy
   pip install lockfile>=0.12.2 gntp>=1.0.3 distro
   pip install WMI>=1.5.1 pywin32
   ```

5. **Generate templates and icons**:
   ```cmd
   cd templates.in
   python make.py
   cd ..\icons.in
   python make.py
   cd ..
   ```

6. **Build with PyInstaller**:
   ```cmd
   pyinstaller --log-level=TRACE --clean TaskCoach.spec
   ```

7. **Test the executable**:
   ```cmd
   dist\TaskCoach\TaskCoach.exe --help
   dist\TaskCoach\TaskCoach.exe --version
   ```

8. **Package for distribution**:
   ```cmd
   # The dist\TaskCoach\ directory contains the complete application
   # Compress to ZIP for distribution
   ```

---

## Linux Build

### Requirements

- **Python**: 3.11 or later
- **wxPython**: 4.2.4 or later (built from source)
- **PyInstaller**: Latest version
- **Platform**: Ubuntu 22.04 or compatible
- **GTK3 Development Libraries**: Required for wxPython build

### System Dependencies

The Linux build requires extensive GTK3 and multimedia libraries:

```bash
sudo apt-get update
sudo apt-get install -y \
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
  libunwind-dev \
  libgstreamer1.0-dev \
  libgstreamer-plugins-base1.0-dev \
  libwebkit2gtk-4.0-dev \
  libxtst-dev
```

**Critical**: `libunwind-dev` is required by `libgstreamer1.0-dev`. Without it, you'll get:
```
E: Unable to correct problems, you have held broken packages.
```

### Automated Build (GitHub Actions)

The workflow runs automatically when you push to the build branch:

```bash
git push -u origin claude/pyinstaller-windows-build-01Czh7R5Phw5PrbYuG68Wxtp
```

**What it does**:
1. Sets up Ubuntu 22.04 with Python 3.11
2. Installs all GTK3/GStreamer development libraries
3. Builds wxPython 4.2.4+ from source (20-30 minutes)
4. Installs PyInstaller and all dependencies
5. Generates templates and icons
6. Builds with `--log-level=TRACE`
7. Tests executable
8. Packages as `TaskCoach-Linux-x64.tar.gz`
9. Uploads artifacts (30-day retention)

**Download the build**:
- Go to GitHub Actions tab
- Find the latest workflow run
- Download `TaskCoach-Linux-x64.tar.gz` from artifacts

### Manual Build (Local Linux)

1. **Install system dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3.11 python3.11-dev python3-pip
   sudo apt-get install -y \
     libgtk-3-dev libglib2.0-dev libcairo2-dev libpango1.0-dev \
     libatk1.0-dev libgdk-pixbuf2.0-dev libnotify-dev libsdl2-dev \
     libjpeg-dev libtiff-dev libpng-dev freeglut3-dev libunwind-dev \
     libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
     libwebkit2gtk-4.0-dev libxtst-dev
   ```

2. **Install wxPython 4.2.4+ (from source)**:
   ```bash
   # This takes 20-30 minutes
   pip install -v "wxPython>=4.2.4"
   python3 -c "import wx; print(wx.version())"
   ```

3. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

4. **Install dependencies**:
   ```bash
   pip install six>=1.16.0 desktop3 pypubsub twisted
   pip install chardet>=5.2.0 python-dateutil>=2.9.0
   pip install pyparsing>=3.1.2 lxml keyring numpy
   pip install lockfile>=0.12.2 gntp>=1.0.3 distro
   ```

5. **Generate templates and icons**:
   ```bash
   cd templates.in && python3 make.py && cd ..
   cd icons.in && python3 make.py && cd ..
   ```

6. **Build with PyInstaller**:
   ```bash
   pyinstaller --log-level=TRACE --clean TaskCoach.spec
   ```

7. **Test the executable**:
   ```bash
   ./dist/TaskCoach/TaskCoach --help
   ./dist/TaskCoach/TaskCoach --version
   ```

8. **Package for distribution**:
   ```bash
   cd dist
   tar -czf TaskCoach-Linux-x64.tar.gz TaskCoach/
   ```

---

## Common Issues

### Issue: PyInstaller hangs at "Looking for dynamic libraries"

**Symptom**: PyInstaller freezes with message "INFO: Looking for dynamic libraries"

**Why**: This is a normal but slow process. PyInstaller analyzes all dependencies.

**Solutions**:
1. **Use TRACE logging** (already enabled in workflows):
   ```bash
   pyinstaller --log-level=TRACE TaskCoach.spec
   ```
   This shows progress and helps identify bottlenecks.

2. **Wait patiently**: Can take 10-30 minutes depending on:
   - System resources (CPU, RAM)
   - Number of dependencies (wxPython has many)
   - Disk I/O speed
   - Antivirus scanning (Windows)

3. **Check the log**: Look at `pyinstaller_trace.log` for:
   - What file it's currently analyzing
   - Any errors or warnings
   - Progress through dependency tree

4. **Temporary workarounds**:
   - Disable antivirus during build (Windows)
   - Use faster disk (SSD recommended)
   - Increase RAM allocation for VM
   - Use GitHub Actions (pre-configured environment)

**Expected timeline**:
- Windows: 5-15 minutes typically
- Linux: 10-30 minutes (wxPython build adds time)

### Issue: Missing wxPython module errors

**Symptom**: Built executable fails with "ModuleNotFoundError: No module named 'wx.lib.agw.hypertreelist'"

**Solution**: Add to `TaskCoach.spec` hidden imports:
```python
hidden_imports = [
    'wx.lib.agw.hypertreelist',
    'wx.lib.masked',
    # ... other wx modules
]
```

### Issue: wxPython version < 4.2.4

**Symptom**: Category backgrounds don't display correctly

**Solution**: Verify and upgrade:
```bash
python -c "import wx; print(wx.version())"
pip install --upgrade "wxPython>=4.2.4"
```

### Issue: Linux - broken packages error

**Symptom**:
```
libgstreamer1.0-dev : Depends: libunwind-dev
E: Unable to correct problems, you have held broken packages
```

**Solution**: Install `libunwind-dev` first:
```bash
sudo apt-get install -y libunwind-dev
sudo apt-get install -y libgstreamer1.0-dev
```

Or use the complete dependency list from the workflow.

### Issue: Data files not included in build

**Symptom**: Missing translations, icons, or templates at runtime

**Solution**: Verify `datas` in `TaskCoach.spec`:
```python
datas = [
    ('i18n.in/*.po', 'i18n.in'),
    ('templates.in/*.tsktmpl', 'templates.in'),
    ('icons.in/*.ico', 'icons.in'),
]
```

Then regenerate:
```bash
cd templates.in && python make.py && cd ..
cd icons.in && python make.py && cd ..
```

---

## GitHub Actions

### Workflow Files

- **Windows**: `.github/workflows/build-windows-exe.yml`
- **Linux**: `.github/workflows/build-linux-exe.yml`

### Triggers

Both workflows trigger on:
- Push to `claude/pyinstaller-windows-build-*` branches
- Pull requests to `main`
- Manual dispatch via GitHub UI

### Artifacts

**Windows build uploads**:
- `TaskCoach-Windows-x64.zip` - Executable bundle (30 days)
- `pyinstaller-trace-log` - TRACE output (7 days)
- `build-debug-files` - Debug files if build fails (7 days)

**Linux build uploads**:
- `TaskCoach-Linux-x64.tar.gz` - Executable bundle (30 days)
- `pyinstaller-trace-log-linux` - TRACE output (7 days)
- `build-debug-files-linux` - Debug files if build fails (7 days)

### Monitoring Builds

1. Go to repository's Actions tab
2. Find the workflow run
3. Click to see real-time logs
4. Download artifacts when complete

### Debugging Failed Builds

1. **Check the workflow logs**:
   - Review each step for errors
   - Look for missing dependencies
   - Check version mismatches

2. **Download trace log**:
   - Contains detailed PyInstaller output
   - Shows exactly where it hangs/fails
   - Includes all import analysis

3. **Download debug files** (on failure):
   - Build directory contents
   - Intermediate files
   - Error logs

---

## Testing Built Executables

### Basic Tests

**Command-line**:
```bash
# Windows
TaskCoach.exe --help
TaskCoach.exe --version

# Linux
./TaskCoach --help
./TaskCoach --version
```

### GUI Tests

1. **Launch application**:
   - Double-click executable (Windows)
   - Run from terminal (Linux)

2. **Create a task**:
   - New task with name and description
   - Add due date
   - Add effort tracking

3. **Test categories**:
   - Create categories with colors
   - Assign to tasks
   - **Verify full-row background coloring** (wxPython 4.2.4+ fix)
   - Check right-aligned columns are fully colored

4. **Test core features**:
   - Save/load task files (.tsk)
   - Export to various formats
   - Preferences and settings
   - Help documentation

---

## PyInstaller Spec File

The `TaskCoach.spec` file configures the build:

```python
# Main entry point
a = Analysis(
    ['taskcoach.py'],
    hiddenimports=[...],  # All required modules
    datas=[...],          # Data files to include
)

# Windows GUI executable
exe = EXE(
    ...,
    console=False,        # No console window
    icon='icons.in/taskcoach.ico',
)

# Bundle everything
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
)
```

### Key Configuration

- **Entry point**: `taskcoach.py`
- **Icon**: `icons.in/taskcoach.ico` (Windows) / `taskcoach.png` (Linux)
- **Console**: Disabled (GUI app)
- **UPX**: Enabled for compression
- **Bundle**: Directory mode (all files in folder)

---

## Distribution

### Windows

**Portable ZIP**:
- Unzip `TaskCoach-Windows-x64.zip`
- Run `TaskCoach.exe` directly
- No installation required

**Installer** (future):
- Use Inno Setup with `build.in/windows/taskcoach.iss`
- Creates traditional Windows installer
- Adds Start Menu shortcuts
- Optional file associations

### Linux

**Portable tarball**:
- Extract `TaskCoach-Linux-x64.tar.gz`
- Run `./TaskCoach` from extracted directory
- No installation required

**System package** (future):
- Create `.deb` package for Debian/Ubuntu
- Create `.rpm` package for Fedora/RHEL
- Add to package repositories

---

## Performance

### Build Time

- **Windows**: 5-15 minutes
  - Python/dependency install: 3-5 min
  - PyInstaller analysis: 2-8 min
  - Package creation: 1-2 min

- **Linux**: 25-45 minutes
  - System packages: 2-3 min
  - wxPython build from source: 20-30 min
  - PyInstaller analysis: 3-10 min
  - Package creation: 1-2 min

### Executable Size

- **Windows**: ~100-200 MB
  - Python runtime: ~30 MB
  - wxPython: ~50-80 MB
  - Other dependencies: ~20-40 MB
  - Application code: ~10-20 MB

- **Linux**: ~120-250 MB
  - Python runtime: ~30 MB
  - wxPython + GTK: ~70-120 MB
  - Other dependencies: ~20-40 MB
  - Application code: ~10-20 MB

### Runtime Performance

- **Startup time**: 2-5 seconds (first run), <1 second (subsequent)
- **Memory usage**: 50-100 MB typical, 100-200 MB with large task files
- **Disk I/O**: Minimal after initial load

---

## Next Steps

1. **Code signing**:
   - Windows: Sign with Authenticode certificate
   - macOS: Notarize for Gatekeeper (future)

2. **Installers**:
   - Windows: Inno Setup or WiX
   - Linux: .deb and .rpm packages
   - macOS: .dmg and .app bundle (future)

3. **Automated releases**:
   - Tag-based release builds
   - Attach executables to GitHub releases
   - Version number automation

4. **Testing**:
   - Automated GUI tests
   - Integration tests for builds
   - Cross-platform compatibility tests

---

## References

- **PyInstaller**: https://pyinstaller.org/
- **wxPython 4.2.4+**: https://wxpython.org/
- **GitHub Actions**: https://docs.github.com/en/actions
- **wxPython Issue #2081**: https://github.com/wxWidgets/Phoenix/issues/2081
- **wxPython PR #2088**: https://github.com/wxWidgets/Phoenix/pull/2088

---

## Support

**Build issues**:
- Check trace log: `pyinstaller_trace.log`
- Review workflow logs in GitHub Actions
- See `CRITICAL_WXPYTHON_PATCH.md` for wxPython issues

**Application issues**:
- See `README.md` for general usage
- See `DEBIAN_BOOKWORM_SETUP.md` for Debian-specific setup
- Open issue on GitHub repository

---

**Last Updated**: 2025-11-17
**Python**: 3.11+
**wxPython**: 4.2.4+
**PyInstaller**: Latest
**Platforms**: Windows 10/11, Ubuntu 22.04+
