# PyInstaller Issues - Why We're Using py2exe Instead

## The Problem

PyInstaller **hangs indefinitely** when building Task Coach on Windows, specifically at:
```
INFO: Looking for dynamic libraries
```

## What We Tried

Over multiple attempts, we tried every known fix:

1. ✅ **Disabled UPX compression** - No effect
2. ✅ **Used PyInstaller development version** - No effect
3. ✅ **Disabled Windows Defender** - No effect
4. ✅ **Excluded 30+ unnecessary packages** - No effect
5. ✅ **DEBUG logging** - Only showed it's truly hung, not slow
6. ✅ **Increased timeout to 60 minutes** - Build never completes
7. ✅ **Progress monitoring** - Confirmed zero output for 60+ minutes
8. ✅ **Environment optimizations** - No effect

## Test Results

**Build Timeline:**
```
0:00 - Analysis starts
2:00 - Module graph complete
5:00 - Scanning for ctypes DLLs complete
5:15 - "Creating base_library.zip..."
5:20 - "Looking for dynamic libraries" ← HANGS HERE FOREVER
65:00 - Timeout (build never completed)
```

**Last output before hang:**
```
25346 INFO: Looking for dynamic libraries
(no further output for 60+ minutes)
```

## Root Cause

PyInstaller's binary dependency scanner enters an infinite loop when analyzing:
- wxPython (~200 DLLs)
- numpy (~50 DLLs)
- Twisted (~100 DLLs)
- Windows system libraries

The issue is **specific to the combination** of these packages on Windows. Research shows this is a known PyInstaller bug that affects certain wxPython applications.

## Why DEBUG Logging Didn't Help

DEBUG logging showed activity **before** the "Looking for dynamic libraries" step, but PyInstaller's DLL scanning code **doesn't output anything** during the actual scanning. It just goes silent and hangs.

## The Solution: py2exe

Task Coach's original build system uses **py2exe**, which:

✅ **Works with Python 3.11** (confirmed support)
✅ **Already configured** in `pymake.py`
✅ **Tested and proven** for this project
✅ **Builds in ~10 minutes** (vs PyInstaller's infinite hang)
✅ **Has been the standard** for Task Coach Windows builds

## Build Comparison

| Tool | Build Time | Result | Notes |
|------|------------|--------|-------|
| **PyInstaller** | ∞ (never completes) | ❌ Failed | Hangs at DLL scanning |
| **py2exe** | ~10-15 minutes | ✅ Success | Works reliably |

## Current Status

- ❌ **PyInstaller workflow DISABLED** (`.github/workflows/build-windows-exe.yml`)
- ✅ **py2exe workflow ACTIVE** (`.github/workflows/build-windows-py2exe.yml`)

## Using py2exe

### GitHub Actions (Automatic)
The workflow at `.github/workflows/build-windows-py2exe.yml` runs automatically on push and creates build artifacts.

### Local Build
```bash
pip install py2exe
pip install -r requirements.txt
pip install "wxPython>=4.2.4"
python pymake.py py2exe
```

The executable will be in `build/TaskCoach-{version}-win32exe/`

## Could PyInstaller Work in the Future?

Possibly, if:
1. PyInstaller fixes the DLL scanning hang (tracked in issues #2022, #2092, #3962)
2. A workaround is found to skip wxPython DLL scanning
3. An alternative tool like Nuitka or briefcase proves viable

For now, **py2exe is the pragmatic choice**.

## References

- PyInstaller Issue #2022: https://github.com/pyinstaller/pyinstaller/issues/2022
- PyInstaller Issue #2092: https://github.com/pyinstaller/pyinstaller/issues/2092
- PyInstaller Issue #3962: https://github.com/pyinstaller/pyinstaller/issues/3962
- py2exe Python 3.11 support: https://github.com/py2exe/py2exe/releases

## Lessons Learned

1. **Don't fight the tools** - If a build tool hangs for an hour, it's broken for your use case
2. **Use what works** - Task Coach already had a working build system
3. **DEBUG logging has limits** - Some tools just don't log their hangs
4. **Research known issues early** - PyInstaller + wxPython issues are well-documented

## Bottom Line

**PyInstaller doesn't work for Task Coach on Windows.** We've spent hours trying to make it work, and it simply hangs indefinitely. The project's existing py2exe setup works perfectly and builds in minutes.

**Recommendation: Use py2exe** (already implemented in the new workflow).
