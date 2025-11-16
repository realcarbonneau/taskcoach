# Building Windows Executable with PyInstaller

This document describes how to build a Windows executable for Task Coach using PyInstaller.

## Overview

Task Coach can now be built as a standalone Windows executable using PyInstaller. This provides an alternative to the traditional py2exe build process and works with modern Python versions.

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
   - Find the latest successful workflow run
   - Download the `TaskCoach-Windows-Executable` artifact

The workflow file is located at: `.github/workflows/build-windows-exe.yml`

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
pip install pyinstaller
pip install distro six desktop3 pypubsub twisted chardet python-dateutil pyparsing lxml keyring numpy lockfile gntp WMI
pip install "wxPython>=4.2.4"
```

**Important:** wxPython 4.2.4 or higher is required for Task Coach. Earlier versions may have critical bugs affecting category row background coloring and other features. See `CRITICAL_WXPYTHON_PATCH.md` for details.

Note: Installing wxPython may take some time as it needs to compile or download platform-specific binaries.

4. Run the build script:
```bash
python build_windows.py
```

The build script will:
- Check all dependencies are installed
- Clean previous build artifacts
- Build the executable using PyInstaller
- Verify the build output
- Create a ZIP archive

#### Build Output

After a successful build, you'll find:
- `dist/TaskCoach/TaskCoach.exe` - The main executable
- `dist/TaskCoach/` - All required files and dependencies
- `TaskCoach-Windows.zip` - A ZIP archive containing everything

#### Manual PyInstaller Build

If you prefer to run PyInstaller manually:

```bash
pyinstaller TaskCoach.spec --clean
```

## PyInstaller Spec File

The `TaskCoach.spec` file contains the build configuration:
- Entry point: `taskcoach.py`
- Includes all taskcoachlib packages
- Bundles icons, translations, and help files
- Excludes unnecessary packages (matplotlib, PIL, PyQt, etc.)
- Configured for Windows GUI application (no console window)

## Troubleshooting

### wxPython Installation Issues

If wxPython fails to install:
```bash
pip install --upgrade pip
pip install wxPython --no-cache-dir
```

On some systems, you may need to install Visual C++ Redistributables:
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Build Failures

If the build fails:
1. Check the build logs for specific error messages
2. Ensure all dependencies are installed: `python build_windows.py` will check for you
3. Try cleaning and rebuilding:
   ```bash
   rmdir /s /q build dist
   pyinstaller TaskCoach.spec --clean
   ```

### Missing Icons or Resources

If the executable is missing icons or other resources:
1. Check that the files exist in the source directory
2. Verify the paths in `TaskCoach.spec`
3. Rebuild with the `--clean` flag

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
