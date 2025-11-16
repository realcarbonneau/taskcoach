"""
Patch PyInstaller to add verbose logging during DLL scanning.
This will show us EXACTLY which module causes the hang.
"""
import os
import sys

# Find PyInstaller's bindepend.py
pyinstaller_path = os.path.dirname(sys.modules['PyInstaller'].__file__)
bindepend_file = os.path.join(pyinstaller_path, 'depend', 'bindepend.py')

print(f"[PATCH] Found bindepend.py at: {bindepend_file}")

# Read the file
with open(bindepend_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Add debug print at the start of the main scanning function
# Look for the function that scans for dependencies
patch_code = '''
import sys
_original_getImports = getImports if 'getImports' in dir() else None

def getImports_patched(pth):
    print(f"[DLL_SCAN] Scanning: {pth}", file=sys.stderr, flush=True)
    result = _original_getImports(pth) if _original_getImports else []
    print(f"[DLL_SCAN] Done: {pth}", file=sys.stderr, flush=True)
    return result

if _original_getImports:
    getImports = getImports_patched
'''

# Check if already patched
if '[DLL_SCAN]' not in content:
    # Add patch at the end of imports section
    import_end = content.find('\n\ndef ')
    if import_end > 0:
        content = content[:import_end] + '\n' + patch_code + content[import_end:]

        # Write back
        with open(bindepend_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("[PATCH] Successfully patched bindepend.py")
    else:
        print("[PATCH] WARNING: Could not find insertion point")
else:
    print("[PATCH] Already patched")
