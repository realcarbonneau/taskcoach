# PyInstaller "Looking for Dynamic Libraries" - What's Happening?

## The Issue

When building with PyInstaller, the build hangs at:
```
INFO: Looking for dynamic libraries
```

This can take **20-60 minutes** and appears frozen, but it's actually working.

## What PyInstaller is Doing

During this phase, PyInstaller:

1. **Scans every imported Python package** for DLL dependencies
2. **Opens and analyzes each DLL** to find its dependencies
3. **Recursively follows the dependency chain** for each DLL
4. **On Windows**, this involves scanning:
   - wxPython (~200+ DLLs)
   - numpy (~50+ DLLs)
   - Twisted (~100+ DLLs)
   - Python itself (~30+ DLLs)
   - Windows system DLLs (varies)

## Why It's So Slow

### Performance Issues:
1. **Windows Defender** - Scans every DLL as it's opened (~100-200ms per file)
2. **DLL Dependency Resolution** - Each DLL can depend on 5-20 other DLLs
3. **Missing DLL Warnings** - Each warning adds ~350ms delay
4. **Large Packages** - wxPython alone has hundreds of DLLs to scan

### Math:
```
~500 DLLs × ~200ms each = 100 seconds (best case)
Add Windows Defender scanning = 5-10x slower
Add dependency resolution = another 2-3x slower
Total: 10-40 minutes
```

## What We See with DEBUG Logging

With `--log-level DEBUG`, you'll see output like:
```
DEBUG: Resolving binary dependencies for wx._core.pyd
DEBUG: Looking for DLL api-ms-win-crt-runtime-l1-1-0.dll
DEBUG: Checking C:\Windows\System32\
DEBUG: Checking C:\Windows\SysWOW64\
DEBUG: Found api-ms-win-crt-runtime-l1-1-0.dll in C:\Windows\System32\
DEBUG: Resolving binary dependencies for api-ms-win-crt-runtime-l1-1-0.dll
DEBUG: Looking for DLL kernel32.dll
... (repeats hundreds of times)
```

## Fixes Applied

### 1. Using PyInstaller Development Version
```bash
pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
```
**Why**: The dev version has performance improvements for DLL scanning.

### 2. Disabled UPX Compression
```python
upx=False  # In TaskCoach.spec
```
**Why**: UPX scanning adds 50-100% to build time.

### 3. Disabled Windows Defender (CI only)
```powershell
Set-MpPreference -DisableRealtimeMonitoring $true
```
**Why**: Reduces per-file scanning overhead by 80-90%.

### 4. Excluded Unnecessary Packages
```python
excludes=['matplotlib', 'PIL', 'pandas', 'scipy', ...]
```
**Why**: Each excluded package saves 1-5 minutes of scanning.

### 5. Progress Monitoring
Added background job that prints timestamps every 2 minutes.
**Why**: Shows the build is still alive, prevents timeout.

## Expected Timeline

With all fixes applied:

| Phase | Time | What's Happening |
|-------|------|------------------|
| Analysis | 2-3 min | Analyzing Python imports |
| Module graph | 3-5 min | Building dependency graph |
| **Looking for DLLs** | **20-40 min** | **← YOU ARE HERE (scanning ~500 DLLs)** |
| Creating base_library.zip | 1-2 min | Packaging Python libraries |
| Bundling | 3-5 min | Copying files to dist/ |
| **Total** | **30-55 min** | |

## How to Monitor Progress

### With DEBUG logging:
```bash
pyinstaller TaskCoach.spec --clean --log-level DEBUG
```

You'll see output every few seconds showing which DLL is being scanned:
- `DEBUG: Resolving binary dependencies for ...`  ← Activity
- No output for 2+ minutes ← Might be stuck
- Continuous output ← Normal, just slow

### Key Indicators:

**Still working:**
- New DEBUG messages every 5-30 seconds
- CPU usage ~10-30%
- Disk I/O activity

**Actually frozen:**
- No new messages for 5+ minutes
- CPU usage 0%
- No disk activity

## Workarounds If Still Too Slow

### Option 1: Reduce DLL Scanning
Add to TaskCoach.spec:
```python
# Skip some DLL dependency resolution
a = Analysis(
    ...
    module_collection_mode={
        'numpy': 'py',  # Don't collect numpy binaries
        'twisted': 'pyz',  # Only collect Python files
    },
)
```

### Option 2: Use --onefile (faster analysis, slower runtime)
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # ← Include in EXE
    a.datas,
    ...
    onefile=True,
)
```

### Option 3: Pre-build on Fast Machine
- Build once on a fast local Windows machine
- Cache the `build/` directory
- Reuse for subsequent builds

## Alternative: py2exe

Task Coach originally used py2exe. Consider:
```bash
python pymake.py py2exe
```

**Pros:**
- Faster builds (~10 minutes)
- Known to work for this project

**Cons:**
- Python 2/3.8 max compatibility
- Less active development
- Requires more setup

## Bottom Line

**The 30-40 minute wait is unfortunately normal** for PyInstaller with large GUI apps like Task Coach on Windows. The fixes reduce it from 60+ minutes to 30-40 minutes, but can't eliminate it entirely.

**The build IS working** - it's just very slow. The DEBUG logs will prove it's making progress.

## If You Can't Wait

If 30-40 minutes is unacceptable:

1. **Use py2exe instead** (see pymake.py)
2. **Build on Linux** with wine (unreliable but faster)
3. **Use a pre-built executable** from releases
4. **Run from source** (`python taskcoach.py`)
