# Building Windows Executable

This document describes how to build a Windows executable for Task Coach.

## ⚠️ Important: Using py2exe (Not PyInstaller)

Task Coach Windows builds use **py2exe**, not PyInstaller. PyInstaller hangs indefinitely during the build process (see `PYINSTALLER_ISSUES.md` for details).

## Overview

Task Coach builds as a standalone Windows executable using py2exe, which works reliably with Python 3.11 and creates a distributable Windows application.

## Build Methods

### Method 1: GitHub Actions (Recommended)

The easiest way to build the Windows executable is through GitHub Actions:

1. Push your changes to the repository
2. The workflow will automatically trigger on:
   - Pushes to `main`, `master`, or `claude/**` branches
   - Pull requests to `main` or `master`
   - Manual workflow dispatch

3. Download the built executable from the Actions artifacts:
   - Go to the Actions tab in GitHub
   - Find the latest successful "Build Windows Executable (py2exe)" workflow run
   - Download the `TaskCoach-Windows-py2exe` artifact

The workflow file is located at: `.github/workflows/build-windows-py2exe.yml`

**Build time:** Approximately 10-15 minutes

### Method 2: Local Build on Windows

To build locally on a Windows machine:

#### Prerequisites

1. **Python 3.8 or higher** (Python 3.11 recommended)
2. **Git** (to clone the repository)

#### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/realcarbonneau/taskcoach.git
cd taskcoach
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install --upgrade pip setuptools wheel
pip install py2exe
pip install distro six desktop3 pypubsub twisted chardet python-dateutil pyparsing lxml keyring numpy lockfile gntp WMI
pip install "wxPython>=4.2.4"
```

**Important:** wxPython 4.2.4 or higher is required for Task Coach. Earlier versions may have critical bugs affecting category row background coloring and other features. See `CRITICAL_WXPYTHON_PATCH.md` for details.

Note: Installing wxPython may take some time as it needs to compile or download platform-specific binaries.

4. Build the executable:
```bash
python pymake.py py2exe
```

The build will:
- Create the executable using py2exe
- Bundle all dependencies
- Create a distributable folder
- Complete in approximately 10-15 minutes

#### Build Output

After a successful build, you'll find:
- `build/TaskCoach-{version}-win32exe/taskcoach.exe` - The main executable
- `build/TaskCoach-{version}-win32exe/` - All required files and dependencies
- The folder can be zipped for distribution

## py2exe Configuration

The `pymake.py` file contains the build configuration:
- Entry point: `taskcoach.pyw` (GUI mode) and `taskcoach_console.py` (console mode)
- Includes all taskcoachlib packages
- Bundles icons, translations, and help files
- Configured for Windows with proper manifest
- Uses compression and optimization level 2

## Troubleshooting

### wxPython Installation Issues

If wxPython fails to install:
```bash
pip install --upgrade pip
pip install wxPython --no-cache-dir
```

On some systems, you may need to install Visual C++ Redistributables:
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

### py2exe Installation Issues

If py2exe fails to install:
```bash
pip install --upgrade pip setuptools wheel
pip install py2exe
```

Verify installation:
```bash
python -c "import py2exe; print(py2exe.__version__)"
```

### Build Failures

If the build fails:
1. Check the error messages for missing dependencies
2. Ensure all dependencies are installed (see step 3 above)
3. Try cleaning and rebuilding:
   ```bash
   rmdir /s /q build
   python pymake.py py2exe
   ```

### Missing Icons or Resources

If the executable is missing icons or other resources:
1. Check that `icons.in/taskcoach.ico` exists
2. Check that translation files exist in `taskcoachlib/i18n/`
3. Verify paths in `pymake.py`
4. Rebuild with clean build directory

## Testing the Executable

After building, test the executable:

1. Navigate to `dist/TaskCoach/`
2. Run `TaskCoach.exe`
3. Test basic functionality:
   - Create a new task
   - Save and load a file
   - Test the UI elements

## Distribution

To distribute the application:

1. Use the `TaskCoach-Windows.zip` file, which contains everything needed
2. Users can extract it anywhere and run `TaskCoach.exe`
3. No Python installation required on user machines

Alternatively, you could create an installer using Inno Setup (see `build.in/windows/taskcoach.iss`).

## Differences from py2exe

PyInstaller offers several advantages over py2exe:
- Works with Python 3.8+
- Cross-platform build system
- Better dependency detection
- Active development and maintenance
- Can be run on CI/CD platforms

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/build-windows-exe.yml`) provides:
- Automated builds on every push
- Artifact retention for 30 days
- Build verification
- Error logging

## Further Information

- PyInstaller documentation: https://pyinstaller.org/
- GitHub Actions: https://docs.github.com/actions
- Task Coach development: See README.md
