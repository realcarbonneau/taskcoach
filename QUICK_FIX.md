# Quick Fix for Task Coach on Debian Bookworm

## Problem

After migrating to Python 3 and wxPython Phoenix, category and task background colors don't fill the entire row - only the text is colored.

## Solution (Choose One)

### ✓ RECOMMENDED: Patch wxPython Library

**What it does:** Patches your installed wxPython 4.2.1 with the fix from wxPython 4.2.4

**Time:** Less than 1 minute

**Status:** ✓ Already applied to this development environment

**For other systems using venv with --system-site-packages:**
```bash
sudo python3 patch-wxpython-simple.py
```

**Details:** See `WXPYTHON_PATCH.md`

---

### Alternative: Upgrade to wxPython 4.2.4

**What it does:** Compiles and installs wxPython 4.2.4 from source

**Time:** 15-30 minutes

**Command:**
```bash
./upgrade-wxpython.sh
```

**Details:** See `WXPYTHON_UPGRADE.md`

---

## What Gets Fixed

After applying the patch or upgrade:

✓ Full-row background colors (not just text)
✓ Right-aligned columns (date fields) fully colored
✓ Background colors span complete window width
✓ No white gaps between colored cells

## Testing

1. Run Task Coach: `python3 taskcoach.py`
2. Create a category with a background color (e.g., light blue)
3. Create tasks in that category
4. Verify all columns have full-width colored backgrounds

## Documentation

- `DEBIAN_BOOKWORM_FIXES.md` - Complete list of all Python 3 fixes applied
- `WXPYTHON_PATCH.md` - Detailed patching instructions and explanation
- `WXPYTHON_UPGRADE.md` - Detailed upgrade instructions (alternative approach)

## Need Help?

Check the comprehensive documentation in `DEBIAN_BOOKWORM_FIXES.md` for:
- Icon transparency fixes
- Version logging improvements
- Background coloring improvements
- Technical details about wxPython Phoenix differences

---

**TL;DR:** Run `sudo python3 patch-wxpython-simple.py` to fix background coloring in less than 1 minute.
