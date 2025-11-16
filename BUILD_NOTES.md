# PyInstaller Build Implementation Notes

## Summary

Successfully implemented PyInstaller Linux executable build for TaskCoach with comprehensive validation and error handling.

## Local Build Status ✅

**Working executable created:** `/home/user/taskcoach/dist/taskcoach` (61MB)

**Test Results:**
```bash
$ xvfb-run -a ./dist/taskcoach --version
Task Coach 1.5.1

$ xvfb-run -a ./dist/taskcoach --help
Usage: taskcoach [options] [.tsk file]
...
```

## Key Issues Identified and Fixed

### Issue 1: Python Version Mismatch

**Problem:** The `python3` command resolves to Python 3.11, but wxPython is only installed for Python 3.12.

```bash
$ which python3
/usr/bin/python3  → links to Python 3.11 (no wxPython)

$ which python3.12
/usr/bin/python3.12 → Python 3.12 (has wxPython 4.2.1)
```

**Solution:** Use `python3.12` explicitly throughout the workflow, not just `python3`.

### Issue 2: PyInstaller "Success" Despite Missing wxPython

**Problem:** PyInstaller completes with exit code 0 even when wxPython modules are not found. It treats missing hidden imports as warnings, not errors:

```
INFO: Analyzing hidden import 'wx._core'
ERROR: Hidden import 'wx._core' not found
...
INFO: Build complete! The results are available in: dist
```

This results in an executable that fails at runtime with:
```
ModuleNotFoundError: No module named 'wx'
```

**Solution:** Added post-build validation step that fails the build if wxPython import errors are detected:

```bash
if grep -q "ERROR: Hidden import 'wx" build/taskcoach/warn-taskcoach.txt; then
  echo "❌ CRITICAL: wxPython modules not found during build!"
  exit 1
fi
```

### Issue 3: Environment Validation

**Problem:** No early detection when wxPython is inaccessible.

**Solution:** Created `check_wxpython.py` script that:
- Verifies wxPython can be imported
- Checks all required wx submodules
- Tests other dependencies
- Fails early with clear error messages

## Files Created

1. **`.github/workflows/build-linux.yml`** - GitHub Actions workflow
2. **`taskcoach.spec`** - PyInstaller specification file
3. **`check_wxpython.py`** - Environment validation script
4. **`PYINSTALLER_BUILD.md`** - Comprehensive documentation
5. **`BUILD_NOTES.md`** - This file

## GitHub Actions Workflow Steps

1. **Install system dependencies** - wxPython and GTK libraries via apt
2. **Verify environment** - Run `check_wxpython.py` to validate setup
3. **Install Python packages** - PyInstaller and dependencies via pip
4. **Build executable** - Run PyInstaller with taskcoach.spec
5. **Verify build** - Check for wxPython import errors in build log
6. **Test executable** - Run with --version flag
7. **Upload artifacts** - Store executable and build info

## Validation Steps Added

### Pre-Build Validation
```python
# check_wxpython.py verifies:
✓ wxPython imports successfully
✓ wx._core, wx._adv, wx._html, wx._grid, wx._aui accessible
✓ wx.lib, wx.lib.agw, wx.lib.agw.hypertreelist accessible
✓ All other dependencies available
```

### Build Validation
```bash
# Fails build if wxPython not bundled:
grep -q "ERROR: Hidden import 'wx" build/taskcoach/warn-taskcoach.txt
```

### Runtime Validation
```bash
# Tests executable actually works:
xvfb-run -a ./dist/taskcoach --version
```

## Technical Details

### Python Environment
- **Ubuntu 24.04 default python3:** 3.11 (no wxPython)
- **Required:** python3.12 with wxPython 4.2.1+
- **wxPython source:** System package `python3-wxgtk4.0`

### PyInstaller Configuration
- **Mode:** One-file executable
- **Console:** False (GUI application)
- **UPX:** Enabled (disabled automatically on Linux due to compatibility)
- **Data files:** Icons from `taskcoachlib/gui/icons/`, help files
- **Hidden imports:** 90+ modules explicitly listed

### Dependencies Bundled
- wxPython 4.2.1 + all submodules
- TaskCoach library (all modules)
- pypubsub, desktop3, twisted, lxml, numpy, keyring
- All other requirements from setup.py

## Lessons Learned

1. **Always use explicit Python paths** when multiple versions are installed
2. **PyInstaller warnings are critical** - treat ERROR: Hidden import as build failures
3. **Early validation saves time** - check environment before attempting build
4. **Test the executable** - don't trust build completion alone
5. **wxPython from system packages** is more reliable than pip build

## Next Steps

- Monitor GitHub Actions build on next workflow run
- If successful, executable will be available as artifact
- Can create releases with executables attached
- Consider adding builds for other Python/wxPython versions

## Build Commands Reference

### Local Build
```bash
# Install dependencies
sudo apt-get install python3-wxgtk4.0 xvfb libgtk-3-dev
python3.12 -m pip install --break-system-packages pyinstaller pypubsub desktop3 ...

# Verify environment
xvfb-run -a python3.12 check_wxpython.py

# Build
python3.12 -m PyInstaller taskcoach.spec

# Test
xvfb-run -a ./dist/taskcoach --version
```

### Clean Build
```bash
rm -rf build dist
python3.12 -m PyInstaller --clean taskcoach.spec
```

## Troubleshooting Quick Reference

| Issue | Check | Solution |
|-------|-------|----------|
| ModuleNotFoundError: wx | `python3.12 -c "import wx"` | Use `python3.12`, not `python3` |
| Hidden import 'wx' not found | Check build warnings | Verify wxPython accessible before build |
| Build succeeds, runtime fails | Test executable | Add validation steps |
| libXss.so.1 not found | Warning in build | Can ignore for headless, or install libxss1 |

---

**Last Updated:** 2025-11-16
**Status:** ✅ Local build working, GitHub Actions workflow updated
**Tested On:** Ubuntu 24.04, Python 3.12.3, wxPython 4.2.1
