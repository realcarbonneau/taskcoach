# Building a Standalone Linux Executable

This guide explains how to create a self-contained Linux executable for Task Coach using PyInstaller. The executable includes Python, wxPython, and all dependencies bundled together.

## Table of Contents

- [Automated Builds (GitHub Actions)](#automated-builds-github-actions)
- [Manual Local Build](#manual-local-build)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

---

## Automated Builds (GitHub Actions)

The project includes a GitHub Actions workflow that automatically builds the Linux executable.

### When Builds Trigger

Builds automatically run on:
- Pushes to `main` or `master` branch
- New version tags (e.g., `v1.5.2`)
- Pull requests (for testing)
- Manual workflow dispatch

### Downloading Built Executables

1. Go to the [Actions tab](../../actions) in the GitHub repository
2. Click on the latest successful "Build Linux Executable" workflow run
3. Download the `taskcoach-linux-x86_64` artifact
4. Extract and run:
   ```bash
   tar -xzf taskcoach-linux-x86_64.tar.gz
   cd taskcoach
   ./taskcoach
   ```

### Manual Workflow Trigger

You can manually trigger a build:

1. Go to **Actions** → **Build Linux Executable**
2. Click **Run workflow**
3. Select the branch
4. Click **Run workflow**

---

## Manual Local Build

### Prerequisites

**System Requirements:**
- Linux (tested on Ubuntu 22.04, Debian 12)
- Python 3.8 or higher
- Git

**Install System Dependencies:**

For Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    libgtk-3-dev \
    libnotify-dev \
    libsdl2-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libwebkit2gtk-4.0-dev \
    freeglut3-dev \
    libsm-dev \
    libxtst-dev \
    libxxf86vm-dev \
    libxss1 \
    patchelf \
    upx-ucl
```

For Fedora/RHEL:
```bash
sudo dnf install -y \
    python3-devel \
    gtk3-devel \
    libnotify-devel \
    SDL2-devel \
    gstreamer1-devel \
    gstreamer1-plugins-base-devel \
    webkit2gtk3-devel \
    freeglut-devel \
    libSM-devel \
    libXtst-devel \
    libXxf86vm-devel \
    libXScrnSaver \
    patchelf \
    upx
```

### Build Steps

1. **Clone the repository:**
   ```bash
   git clone --depth 1 https://github.com/taskcoach/taskcoach.git
   cd taskcoach
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   # Upgrade pip
   pip install --upgrade pip setuptools wheel

   # Install wxPython (for Ubuntu 22.04)
   pip install -U \
       -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 \
       wxPython

   # For other distributions, visit: https://wxpython.org/pages/downloads/

   # Install PyInstaller
   pip install pyinstaller

   # Install Task Coach dependencies
   pip install -e .
   ```

4. **Build the executable:**
   ```bash
   pyinstaller taskcoach-linux.spec
   ```

5. **Test the build:**
   ```bash
   ./dist/taskcoach/taskcoach
   ```

6. **Create a distributable archive:**
   ```bash
   cd dist
   tar -czf taskcoach-linux-x86_64.tar.gz taskcoach/
   ```

---

## Distribution

The resulting executable is in `dist/taskcoach/`. This directory contains:

- `taskcoach` - The main executable
- All required libraries and dependencies
- Data files (translations, icons, templates)

### Distribution Methods

**Method 1: Archive (Recommended)**

Create a tarball:
```bash
cd dist
tar -czf taskcoach-linux-x86_64.tar.gz taskcoach/
```

Users can extract and run:
```bash
tar -xzf taskcoach-linux-x86_64.tar.gz
cd taskcoach
./taskcoach
```

**Method 2: Create a Desktop Entry**

Create `~/.local/share/applications/taskcoach.desktop`:
```desktop
[Desktop Entry]
Name=Task Coach
Comment=Your friendly task manager
Exec=/path/to/taskcoach/taskcoach
Icon=/path/to/taskcoach/icons.in/taskcoach.png
Terminal=false
Type=Application
Categories=Office;ProjectManagement;
```

**Method 3: AppImage (Future Enhancement)**

The PyInstaller output can be packaged as an AppImage for maximum portability.

---

## Troubleshooting

### Build Issues

**Problem: wxPython installation fails**

Try installing from source:
```bash
pip install --upgrade --pre -f https://wxpython.org/Phoenix/snapshot-builds/ wxPython
```

Or use your distribution's package:
```bash
# Ubuntu/Debian
sudo apt-get install python3-wxgtk4.0

# Fedora
sudo dnf install python3-wxpython4
```

**Problem: Missing system libraries**

Check which libraries are missing:
```bash
ldd dist/taskcoach/taskcoach
```

Install any missing dependencies with your package manager.

**Problem: "ImportError" when running the executable**

Add verbose output to see what's failing:
```bash
./dist/taskcoach/taskcoach --debug
```

Or rebuild with debugging:
```bash
pyinstaller --debug all taskcoach-linux.spec
```

### Runtime Issues

**Problem: Application doesn't start**

Run from terminal to see error messages:
```bash
cd dist/taskcoach
./taskcoach
```

**Problem: Fonts or icons look wrong**

Ensure the icon and data files were included:
```bash
ls -la dist/taskcoach/icons.in/
ls -la dist/taskcoach/templates.in/
```

**Problem: Translations missing**

Check i18n files:
```bash
ls -la dist/taskcoach/taskcoachlib/i18n/
```

---

## Technical Details

### What Gets Bundled

The PyInstaller build includes:

- **Python Interpreter**: Complete Python runtime (no system Python needed)
- **Libraries**: wxPython, Twisted, and all dependencies
- **Data Files**:
  - Translations (i18n)
  - Templates
  - Icons and images
  - Help files
- **Task Coach Code**: All taskcoachlib modules

### Excluded Modules

To reduce size, these are excluded:
- tkinter
- matplotlib
- PyQt5/PyQt6
- PySide2/PySide6

### Build Optimizations

- **UPX Compression**: Reduces executable size (~30-40% smaller)
- **No Debug Symbols**: Stripped for smaller size
- **Selective Imports**: Only necessary modules included

### Compatibility

The executable should work on:
- ✅ Ubuntu 20.04+
- ✅ Debian 11+
- ✅ Fedora 35+
- ✅ Linux Mint 20+
- ✅ Other modern Linux distributions with GTK3

**Requirements on target system:**
- GTK3 libraries (usually pre-installed)
- X11 or Wayland
- glibc 2.31+ (most modern distros)

---

## Comparison to Traditional Packages

| Method | Pros | Cons |
|--------|------|------|
| **PyInstaller** | ✅ Works everywhere<br>✅ No dependencies<br>✅ Self-contained | ❌ Larger size (~150-200MB)<br>❌ Manual updates |
| **DEB/RPM** | ✅ Small size<br>✅ System integration<br>✅ Auto updates | ❌ Distribution-specific<br>❌ Dependency issues |
| **Source Install** | ✅ Smallest footprint<br>✅ Latest Python | ❌ Complex setup<br>❌ Dependency hell |
| **Flatpak** | ✅ Sandboxed<br>✅ Auto updates | ❌ Requires Flatpak<br>❌ Large size |

---

## Future Enhancements

Potential improvements to the build system:

- [ ] Create AppImage packages
- [ ] Add ARM64 builds
- [ ] Implement delta updates
- [ ] Create a single-file executable option
- [ ] Add digital signatures
- [ ] Build for older Linux distributions

---

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [wxPython Downloads](https://wxpython.org/pages/downloads/)
- [GitHub Actions Workflow](.github/workflows/build-linux-executable.yml)
- [PyInstaller Spec File](taskcoach-linux.spec)

---

## License

This build configuration is part of Task Coach and is licensed under the GNU General Public License v3.0.
