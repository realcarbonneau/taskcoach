# PyInstaller TRACE Logging - Debugging the Hang

## What We're Using

Instead of `strace` (Linux-only), we're using PyInstaller's built-in **TRACE logging** on Windows.

### Command
```bash
pyinstaller TaskCoach.spec --clean --log-level=TRACE --debug=all
```

### What It Shows

**TRACE level** (maximum verbosity) shows:
- Every file being scanned
- Every DLL being probed
- Every import hook being run
- Every path being searched
- Every binary dependency check
- Every module being analyzed

**--debug=all** adds:
- Bootloader debugging output
- Bindery step details
- Internal PyInstaller state

## How to Read the Output

### Normal Flow (Not Hung)

You'll see continuous output like:
```
TRACE: Scanning for imports in module: taskcoachlib.gui.mainwindow
TRACE: Processing hook for module: wx
TRACE: Looking for binary: wx._core.pyd
TRACE: Found binary at: C:\...\site-packages\wx\_core.pyd
TRACE: Analyzing binary dependencies for: wx._core.pyd
TRACE: Found dependency: python311.dll
TRACE: Found dependency: KERNEL32.dll
... (continues)
```

### When Hung

The last lines will show:
```
TRACE: Analyzing binary dependencies for: some_problem.dll
TRACE: Looking for dependency: missing_or_slow.dll
(no more output - HUNG HERE)
```

## What to Look For

### 1. Last File/DLL Mentioned

If the log ends with:
```
TRACE: Analyzing binary dependencies for: wx._core.pyd
```

Then `wx._core.pyd` is likely the problem.

### 2. Repeated Operations

If you see the same operation 100+ times:
```
TRACE: Searching for: api-ms-win-*.dll
TRACE: Searching for: api-ms-win-*.dll
TRACE: Searching for: api-ms-win-*.dll
... (infinite loop)
```

This indicates a search loop bug.

### 3. Hook Execution

If it hangs during a hook:
```
TRACE: Running hook for: twisted
(no more output)
```

Then the Twisted hook is the problem.

### 4. Path Scanning

If it hangs scanning a directory:
```
TRACE: Scanning directory: C:\some\path\with\many\files
(no more output)
```

Then that directory has too many files or a permission issue.

## Where to Find the Log

After the GitHub Actions workflow runs (or times out):

1. Go to **Actions** tab
2. Click on the latest **Build Windows Executable (PyInstaller)** run
3. Check the **build step output** - last 200 lines will be shown
4. Download **pyinstaller-trace-log** artifact for full log

## Common Patterns

### Pattern 1: pefile Regression

If you see:
```
TRACE: Loading PE file: C:\...\some.dll
TRACE: Calling pefile.PE(...)
(hang - garbage collection loop)
```

**Solution:** Already applied - `pip install "pefile!=2024.8.26"`

But if pefile version check shows 2024.8.26, then the pip constraint didn't work.

### Pattern 2: wxPython DLL Hell

If you see:
```
TRACE: Analyzing dependencies for: wx._core.pyd
TRACE: Found 150 DLL dependencies
TRACE: Resolving: api-ms-win-crt-runtime-l1-1-0.dll
TRACE: Searching in: C:\Windows\System32
TRACE: Searching in: C:\Windows\SysWOW64
... (hangs during search)
```

**Solution:** Exclude some Windows system DLLs from scanning.

### Pattern 3: Twisted Hooks

If you see:
```
TRACE: Running pre-safe-import hook for: twisted
TRACE: Importing twisted.python.modules
(hang during import)
```

**Solution:** Twisted's import hooks might be triggering slow operations.

### Pattern 4: NumPy Binary Scanning

If you see:
```
TRACE: Collecting binaries from: numpy
TRACE: Scanning: C:\...\site-packages\numpy\.libs\
(hang - too many DLLs)
```

**Solution:** Exclude numpy binary collection or provide explicit paths.

## Next Steps Based on Findings

### If It Hangs on a Specific DLL

Add to TaskCoach.spec:
```python
excludes=['problematic_module']
```

### If It Hangs During Binary Dependency Analysis

Add to TaskCoach.spec:
```python
a = Analysis(
    ...
    # Skip binary dependency analysis for specific modules
    module_collection_mode={
        'numpy': 'py',      # Python files only, no binaries
        'twisted': 'pyz',   # PYZ archive, no separate binaries
    }
)
```

### If It's a pefile Issue

Verify pefile version in the workflow output:
```
Verifying critical package versions...
pefile version: X.X.X  ← should NOT be 2024.8.26
```

If it IS 2024.8.26, the constraint didn't work. Try:
```bash
pip uninstall pefile -y
pip install "pefile<2024.8.26"
```

### If It's a Search Loop

Add explicit binary paths:
```python
a = Analysis(
    ...
    binaries=[
        ('path/to/specific.dll', '.'),
    ],
)
```

## Alternative: Use py2exe

If PyInstaller continues to hang despite debugging:

**py2exe workflow** (`.github/workflows/build-windows-py2exe.yml`) should work:
- Uses different build approach
- No DLL scanning phase
- Proven to work with Task Coach
- Builds in 10-15 minutes

Run it manually:
```bash
python pymake.py py2exe
```

## Timeline

With TRACE logging:
- **Log size:** ~50-200 MB (lots of output)
- **Build time (if working):** 15-20 minutes (slower with TRACE)
- **Timeout:** 30 minutes
- **Download artifact:** Full trace log available after run

The trace will definitively show where PyInstaller hangs.
