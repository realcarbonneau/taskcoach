# Process Monitor Tracing - Finding the Exact Hang

## What Is Process Monitor?

**Process Monitor (procmon.exe)** is the Windows equivalent of `strace`. It captures EVERY file, registry, and network operation in real-time.

From SysInternals: https://learn.microsoft.com/en-us/sysinternals/downloads/procmon

## How It Works

1. **Process Monitor starts** before PyInstaller
2. **Captures all file operations** as PyInstaller runs
3. **When PyInstaller hangs**, we kill it and stop Process Monitor
4. **The trace shows** the exact file operation where it hung

## What The Trace Will Show

### Normal Operation (Not Hung)

```csv
Process,Operation,Path,Result
python.exe,CreateFile,C:\...\wx\_core.pyd,SUCCESS
python.exe,ReadFile,C:\...\wx\_core.pyd,SUCCESS
python.exe,CloseFile,C:\...\wx\_core.pyd,SUCCESS
python.exe,CreateFile,C:\...\python311.dll,SUCCESS
python.exe,ReadFile,C:\...\python311.dll,SUCCESS
... (continues)
```

### When Hung

```csv
Process,Operation,Path,Result
python.exe,CreateFile,C:\...\some.dll,SUCCESS
python.exe,ReadFile,C:\...\some.dll,SUCCESS
python.exe,CreateFile,C:\...\problem.dll,SUCCESS
python.exe,ReadFile,C:\...\problem.dll,PENDING
(no more entries - HUNG HERE)
```

**The last file in the trace is the problem.**

## Reading The Output

### In GitHub Actions

After the workflow runs, check the step **"Analyze Process Monitor trace"**:

```
=== LAST 100 FILE OPERATIONS BEFORE HANG ===
python.exe  ReadFile  C:\Windows\System32\kernel32.dll  SUCCESS
python.exe  ReadFile  C:\...\site-packages\wx\_core.pyd  SUCCESS
python.exe  ReadFile  C:\...\some_problem.dll  PENDING
```

**The LAST file operation** shows where PyInstaller hung.

### Download Full Trace

Artifact: **process-monitor-trace**

Contains:
- `procmon.csv` - Human-readable CSV with all operations
- `procmon.pml` - Full binary trace (can open in Process Monitor GUI)
- `build.log` - PyInstaller stdout
- `build.err` - PyInstaller stderr

### Analyzing procmon.csv

Open in Excel or text editor, sort by Time, look at last entries:

**Column meanings:**
- **Process**: python.exe, pyinstaller.exe, etc.
- **Operation**: CreateFile, ReadFile, QueryInformation, etc.
- **Path**: Full path to file being accessed
- **Result**: SUCCESS, PENDING, ACCESS_DENIED, etc.

## Common Hang Patterns

### Pattern 1: Stuck Reading a DLL

```
python.exe  ReadFile  C:\...\numpy\.libs\openblas.dll  PENDING
```

**Solution:** The DLL is corrupted or locked. Exclude numpy binaries.

### Pattern 2: Stuck Querying File Info

```
python.exe  QueryInformationFile  C:\...\wx\_core.pyd  PENDING
```

**Solution:** File permissions issue or antivirus blocking.

### Pattern 3: Infinite Loop on Same File

```
python.exe  ReadFile  C:\...\api-ms-win-crt.dll  SUCCESS
python.exe  ReadFile  C:\...\api-ms-win-crt.dll  SUCCESS
python.exe  ReadFile  C:\...\api-ms-win-crt.dll  SUCCESS
... (repeats 1000+ times)
```

**Solution:** Dependency resolution loop. Exclude system DLLs.

### Pattern 4: Network Operation

```
python.exe  TCP Connect  remote-server:443  PENDING
```

**Solution:** PyInstaller trying to download something. Check hooks.

## What To Do With The Results

### If It Hangs on a Specific DLL

Example: `C:\...\site-packages\numpy\.libs\openblas.dll`

**Fix in TaskCoach.spec:**
```python
excludes=['numpy']
# or
a = Analysis(
    ...
    module_collection_mode={'numpy': 'py'}  # Skip numpy binaries
)
```

### If It Hangs on a Windows System DLL

Example: `C:\Windows\System32\api-ms-win-crt-runtime.dll`

**Fix in TaskCoach.spec:**
```python
a = Analysis(
    ...
    binaries=[],  # Don't auto-collect binaries
)
```

### If It's a File Lock/Permission Issue

Example: Result = `ACCESS_DENIED` or `SHARING_VIOLATION`

**Check:**
- Antivirus blocking the file
- Another process has file open
- File permissions

### If It's an Infinite Loop

Example: Same file accessed 100+ times

**This is a PyInstaller bug** - file an issue with:
- The trace showing the loop
- The specific file causing it

## Comparing to Previous Attempts

### What We Tried Before

1. ❌ **TRACE logging** - PyInstaller doesn't log during DLL scan
2. ❌ **DEBUG logging** - Same issue
3. ❌ **pefile version fix** - Didn't solve the hang
4. ❌ **Excluding packages** - Didn't identify root cause

### What Process Monitor Does

✅ **Shows EXACTLY which file** PyInstaller is accessing
✅ **Shows the operation type** (read, query, etc.)
✅ **Shows if it succeeds or hangs**
✅ **Works even when PyInstaller is silent**

## Technical Details

### Process Monitor Command Line

```powershell
# Start capturing
Procmon64.exe /BackingFile procmon.pml /Quiet /Minimized

# Convert to CSV
Procmon64.exe /OpenLog procmon.pml /SaveAs procmon.csv
```

### Filtering (Not Used)

We capture EVERYTHING because we don't know what will cause the hang. The file is large (~100-500 MB) but shows complete picture.

### Performance Impact

Process Monitor adds ~5-10% overhead. This is acceptable for debugging.

## Next Steps After Results

1. **Identify the problematic file** from last trace entries
2. **Exclude it** from PyInstaller build
3. **Re-run build** to verify fix
4. **If it hangs on different file**, repeat process

This is the definitive debugging approach - no more guessing.

## Example: Real Hang Diagnosis

**Trace shows:**
```
python.exe  CreateFile  C:\...\twisted\python\modules.py  SUCCESS
python.exe  ReadFile    C:\...\twisted\python\modules.py  SUCCESS
python.exe  CreateFile  C:\...\twisted\internet\iocpreactor\tcp.py  SUCCESS
python.exe  ReadFile    C:\...\twisted\internet\iocpreactor\tcp.py  PENDING
```

**Diagnosis:** PyInstaller hung reading `tcp.py` in twisted

**Solution:**
```python
excludes=['twisted.internet.iocpreactor']
```

**Result:** Build completes successfully

This level of detail was impossible with logging alone.
