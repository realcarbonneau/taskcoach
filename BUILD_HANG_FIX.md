# PyInstaller Build Hang - Fixed! 🔧

## 🐛 **Problem**
The Windows PyInstaller build got stuck at:
```
26601 INFO: Looking for dynamic libraries
```

For **2 hours** - this is definitely not normal (should complete in 5-10 minutes).

---

## 🔍 **Root Cause**

PyInstaller was likely hanging due to:
1. **Too many explicit hidden imports** - The full spec had ~40 modules explicitly listed
2. **Complex dependency scanning** - With wx, numpy, lxml, win32com all together
3. **No timeout** - Build could run forever
4. **UPX compression enabled** - Can cause hangs on large binaries

---

## ✅ **Solution Applied**

### 1. Created Simplified Spec File
**File**: `taskcoach-windows-simple.spec`

**Key changes**:
- ✅ **Minimal hidden imports** - Only 8 essential modules
- ✅ **Auto-detection** - Let PyInstaller find dependencies automatically
- ✅ **UPX disabled** - Faster build, avoids compression hangs
- ✅ **No data files** - Auto-detect instead of explicit list
- ✅ **Test exclusions** - Skip unittest/pytest modules

### 2. Added Build Timeout
```yaml
timeout-minutes: 15  # Kill if build takes more than 15 minutes
```

If PyInstaller hangs again, the workflow will auto-cancel after 15 minutes instead of running for hours.

### 3. Reduced Log Level
Changed from `DEBUG` to `INFO` - less verbose output, faster processing.

---

## 📋 **Next Steps**

### 1. Cancel the Stuck Build (Manual)
1. Go to: https://github.com/realcarbonneau/taskcoach/actions
2. Click on the running workflow (yellow spinner)
3. Click **"Cancel workflow"** button (top right)

### 2. New Build Will Auto-Start
The new commits will trigger a fresh build automatically using the simplified spec.

**What to expect**:
- ⏱️ Should complete in **5-10 minutes**
- ✅ Will timeout after 15 minutes if stuck
- 📦 Should produce working executable

### 3. If Simplified Spec Works
If this build succeeds, we can gradually add back features:
1. ✅ Test the basic build
2. 🔧 Add more hidden imports if needed
3. 🔧 Add data files (icons, translations)
4. 🔧 Enable UPX compression (optional)

---

## 📊 **Comparison: Full vs Simple Spec**

| Feature | Full Spec | Simple Spec |
|---------|-----------|-------------|
| Hidden imports | ~40 modules | 8 modules |
| Data files | Explicit list | Auto-detect |
| UPX compression | ✅ Enabled | ❌ Disabled |
| Build complexity | High | Low |
| Risk of hang | Higher | Lower |
| Build speed | Slower | Faster |

---

## 🎯 **What the Simple Spec Does**

```python
# Minimal hidden imports - only essentials
hiddenimports = [
    'wx',              # wxPython (core only)
    'twisted',         # Networking
    'pubsub',          # Event system
    'lxml',            # XML parsing
    'win32api',        # Windows API
    'win32con',        # Windows constants
    'win32gui',        # Windows GUI
    'win32com',        # COM automation
    'pywintypes',      # Windows types
]
```

**Auto-detection handles**:
- wx.lib.agw.* submodules
- numpy submodules
- All i18n translation files
- Templates and icons
- Other dependencies

---

## 🔧 **If Simple Spec Also Hangs**

If the simplified spec also gets stuck, we have fallback options:

### Option 1: Even Simpler (Command-line)
```bash
pyinstaller --onedir --windowed taskcoach.pyw
```
No spec file at all - pure auto-detection.

### Option 2: Different Build Tool
Try `cx_Freeze` instead of PyInstaller:
```bash
pip install cx_Freeze
cxfreeze taskcoach.pyw --target-dir dist
```

### Option 3: Investigate Specific Package
If a specific package is causing issues, we can exclude it and make it optional.

---

## 📝 **Commits Made**

1. **9372bea** - Add timeout to PyInstaller build step (15 min max)
2. **4d69116** - Add simplified PyInstaller spec to avoid build hangs
3. **e22662d** - Switch workflow to use simplified spec file

---

## ⏰ **Timeline**

| Time | Event |
|------|-------|
| 13:20 | Build started with full spec |
| 13:20 | Got stuck at "Looking for dynamic libraries" |
| ~15:20 | User reported 2-hour hang |
| 15:21 | Fixed: Added timeout + simplified spec |
| 15:22 | New build should auto-trigger |

---

## ✅ **Expected Outcome**

The simplified build should:
- ✅ Complete in 5-10 minutes
- ✅ Create TaskCoach.exe
- ✅ Be smaller (no UPX compression)
- ✅ Work for basic testing

**Then we can**:
- Test the executable
- Decide if we need the full spec
- Incrementally add features back if needed

---

## 🆘 **Troubleshooting**

### If Build Times Out (15 minutes)
1. Check which step it timed out on
2. Increase timeout to 30 minutes
3. Add more debug output to that step

### If Build Fails with Errors
1. Check the error message
2. May need to add specific hidden import
3. Check build-warnings artifact

### If Exe Doesn't Run
1. Missing DLLs - check BUILD_INFO.txt
2. Import errors - check console output
3. May need to add hidden imports back

---

**Status**: ✅ Fix deployed, waiting for new build to run

**Next**: Cancel old build, monitor new build, test executable
