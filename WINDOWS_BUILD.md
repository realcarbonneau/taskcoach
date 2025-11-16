# TaskCoach Windows Build with PyInstaller

This document explains how to build TaskCoach as a standalone Windows executable using PyInstaller.

## Overview

The Windows build process uses PyInstaller to create a self-contained executable that includes Python, wxPython, and all dependencies. This allows users to run TaskCoach on Windows without installing Python.

## Requirements

- **Python**: 3.11 or later
- **wxPython**: 4.2.4 or later (CRITICAL - see below)
- **PyInstaller**: Latest version
- **All TaskCoach dependencies** (see setup.py)

### Critical: wxPython 4.2.4+

**You MUST use wxPython 4.2.4 or later** for the Windows build. Earlier versions (including 4.2.0 shipped with Debian Bookworm) have critical bugs affecting category row background coloring:

- **Issue #2081**: `TR_FULL_ROW_HIGHLIGHT` flag doesn't draw item backgrounds
- **Issue #1898**: `TR_FILL_WHOLE_COLUMN_BACKGROUND` doesn't fill right-aligned columns

These issues were fixed in wxPython 4.2.4 via PR #2088. See `CRITICAL_WXPYTHON_PATCH.md` for details.

On Windows, you can install wxPython 4.2.4+ directly via pip:
```bash
pip install "wxPython>=4.2.4"
```

## Build Process

### Automated Build (GitHub Actions)

The easiest way to build is using GitHub Actions:

1. **Push to the build branch**:
   ```bash
   git push -u origin claude/pyinstaller-windows-build-01Czh7R5Phw5PrbYuG68Wxtp
   ```

2. **GitHub Actions will automatically**:
   - Set up a Windows environment
   - Install Python 3.11
   - Install wxPython 4.2.4+
   - Install all dependencies
   - Run PyInstaller with TRACE logging
   - Upload the executable as an artifact

3. **Download the build**:
   - Go to the Actions tab in GitHub
   - Find the latest workflow run
   - Download `TaskCoach-Windows-x64.zip` from artifacts

### Manual Build (Local Windows)

If you want to build locally on Windows:

1. **Install Python 3.11**:
   - Download from https://www.python.org/downloads/
   - Make sure to add Python to PATH

2. **Install wxPython 4.2.4+**:
   ```cmd
   pip install "wxPython>=4.2.4"
   ```

3. **Install PyInstaller**:
   ```cmd
   pip install pyinstaller
   ```

4. **Install dependencies**:
   ```cmd
   pip install six>=1.16.0 desktop3 pypubsub twisted chardet>=5.2.0
   pip install python-dateutil>=2.9.0 pyparsing>=3.1.2 lxml keyring
   pip install numpy lockfile>=0.12.2 gntp>=1.0.3 distro WMI>=1.5.1
   pip install pywin32
   ```

5. **Generate templates** (if needed):
   ```cmd
   cd templates.in
   python make.py
   cd ..
   ```

6. **Generate icons** (if needed):
   ```cmd
   cd icons.in
   python make.py
   cd ..
   ```

7. **Build with PyInstaller**:
   ```cmd
   pyinstaller --log-level=TRACE --clean TaskCoach.spec
   ```

8. **Find the executable**:
   - The built application will be in `dist/TaskCoach/`
   - Run `TaskCoach.exe` to test

## PyInstaller Spec File

The build configuration is in `TaskCoach.spec`. Key features:

- **Main script**: `taskcoach.py`
- **Icon**: `icons.in/taskcoach.ico`
- **Data files included**:
  - Translation files from `i18n.in/*.po`
  - Templates from `templates.in/*.tsktmpl`
  - Icons from `icons.in/`
- **Hidden imports**: All wxPython modules and dependencies
- **Console**: Disabled (GUI application)
- **UPX compression**: Enabled

## Troubleshooting

### Issue: PyInstaller hangs at "Looking for dynamic libraries"

**Symptom**: PyInstaller appears to freeze with the message "INFO: Looking for dynamic libraries"

**Solution**: This is why we use `--log-level=TRACE` in the build:
- TRACE logging shows exactly what PyInstaller is doing
- The process may take 10-30 minutes depending on the system
- Check `pyinstaller_trace.log` for detailed output
- Look for any errors or warnings that might indicate the issue

Common causes:
1. **Antivirus interference**: Disable antivirus temporarily during build
2. **Large dependency tree**: wxPython and numpy have many dependencies
3. **Network access**: PyInstaller may try to download type stubs
4. **Disk I/O**: Building creates thousands of files

**Workarounds**:
- Use `--clean` flag to start fresh
- Increase timeout in GitHub Actions (currently 60 minutes)
- Try building on a different machine/VM
- Check system resources (RAM, disk space)

### Issue: Missing module errors

**Symptom**: Built executable fails with "ModuleNotFoundError"

**Solution**: Add the missing module to `hiddenimports` in `TaskCoach.spec`:
```python
hidden_imports = [
    # ... existing imports ...
    'missing_module_name',
]
```

### Issue: wxPython version mismatch

**Symptom**: Category row backgrounds don't display correctly

**Solution**: Verify wxPython version is 4.2.4+:
```bash
python -c "import wx; print(wx.version())"
```

If version is < 4.2.4, upgrade:
```bash
pip install --upgrade "wxPython>=4.2.4"
```

### Issue: Data files not included

**Symptom**: Missing translations, icons, or templates

**Solution**: Check that data files are being collected in `TaskCoach.spec`:
```python
datas = [
    ('i18n.in/*.po', 'i18n.in'),
    ('templates.in/*.tsktmpl', 'templates.in'),
    ('icons.in/*.ico', 'icons.in'),
]
```

## GitHub Actions Workflow

The workflow is defined in `.github/workflows/build-windows-exe.yml`.

### Workflow Features

1. **Automatic triggers**:
   - Push to `claude/pyinstaller-windows-build-*` branches
   - Pull requests to `main`
   - Manual trigger via workflow_dispatch

2. **Build steps**:
   - Checkout code
   - Set up Python 3.11
   - Install wxPython 4.2.4+
   - Install PyInstaller
   - Install all dependencies
   - Generate templates and icons
   - Build with TRACE logging
   - Test the executable
   - Package as ZIP
   - Upload artifacts

3. **Artifacts uploaded**:
   - `TaskCoach-Windows-x64.zip`: The built application (30 days retention)
   - `pyinstaller-trace-log`: TRACE output for debugging (7 days retention)
   - `build-debug-files`: Build files if build fails (7 days retention)

4. **Timeout protection**:
   - Build step: 60 minutes
   - Test step: 5 minutes

### Debugging Failed Builds

If a build fails:

1. **Download the trace log**:
   - Go to GitHub Actions → Failed workflow run
   - Download `pyinstaller-trace-log` artifact
   - Review `pyinstaller_trace.log` for errors

2. **Check the build output**:
   - Look at the workflow logs in GitHub
   - Check the "Check build output" step
   - Verify all dependencies were installed

3. **Common issues**:
   - Missing dependencies
   - wxPython version < 4.2.4
   - Antivirus blocking PyInstaller
   - Timeout (increase in workflow YAML)

## Testing the Built Executable

After building, test the executable:

1. **Command-line tests**:
   ```cmd
   TaskCoach.exe --help
   TaskCoach.exe --version
   ```

2. **GUI tests**:
   - Launch TaskCoach.exe
   - Create a new task
   - Assign a category with a color
   - Verify category row backgrounds are fully colored
   - Test other core functionality

3. **Verify wxPython fixes**:
   - Create tasks in different categories
   - Ensure full-row background coloring works
   - Check that right-aligned columns (dates) are fully colored
   - No white gaps between columns

## File Structure

```
taskcoach/
├── .github/
│   └── workflows/
│       └── build-windows-exe.yml    # GitHub Actions workflow
├── TaskCoach.spec                   # PyInstaller spec file
├── taskcoach.py                     # Main entry point
├── icons.in/
│   ├── taskcoach.ico               # Windows icon
│   └── ...
├── i18n.in/
│   ├── *.po                        # Translation files
│   └── ...
├── templates.in/
│   ├── *.tsktmpl                   # Task templates
│   └── ...
└── taskcoachlib/                   # Main application code
    └── ...
```

## Distribution

After building:

1. **Extract the ZIP**:
   - Unzip `TaskCoach-Windows-x64.zip`
   - Contains `TaskCoach/` directory with all files

2. **Run the application**:
   - Double-click `TaskCoach.exe`
   - No installation required
   - All dependencies are bundled

3. **Distribution options**:
   - Create an installer with Inno Setup (see `build.in/windows/taskcoach.iss`)
   - Distribute as portable ZIP
   - Upload to releases page

## Performance Notes

- **Build time**: 10-30 minutes depending on system
- **Executable size**: ~100-200 MB (includes Python + wxPython + dependencies)
- **Startup time**: 2-5 seconds on first run, faster on subsequent runs
- **Memory usage**: ~50-100 MB typical usage

## Next Steps

1. **Create installer**: Use Inno Setup to create a Windows installer
2. **Code signing**: Sign the executable for Windows SmartScreen
3. **Automated testing**: Add tests to verify the built executable
4. **Release automation**: Auto-publish releases on tags

## References

- **PyInstaller Documentation**: https://pyinstaller.org/
- **wxPython 4.2.4 Release Notes**: https://wxpython.org/Phoenix/docs/html/
- **wxPython Issue #2081**: https://github.com/wxWidgets/Phoenix/issues/2081
- **wxPython PR #2088**: https://github.com/wxWidgets/Phoenix/pull/2088
- **GitHub Actions**: https://docs.github.com/en/actions

## Support

For build issues:
- Check the trace log: `pyinstaller_trace.log`
- Review GitHub Actions workflow logs
- See `CRITICAL_WXPYTHON_PATCH.md` for wxPython-specific issues
- Open an issue on the GitHub repository

---

**Last Updated**: 2025-11-16
**Build System**: GitHub Actions on windows-latest
**Python Version**: 3.11
**wxPython Version**: 4.2.4+
**PyInstaller Version**: Latest
