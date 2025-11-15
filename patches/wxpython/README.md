# wxPython Patch for Full-Row Background Coloring

This directory contains a patched version of wxPython's `hypertreelist.py` file.

## What This Fixes

The patch applies the fix from wxPython PR #2088 (included in wxPython 4.2.4) to wxPython 4.2.1:

- ✓ Full-row background colors (not just text backgrounds)
- ✓ Right-aligned columns (date fields) now fully colored
- ✓ Background colors span complete window width
- ✓ No white gaps between colored cells

## Changes Made

**File**: `hypertreelist.py` (line ~3011)

**Original code**:
```python
elif drawItemBackground:
    pass
    # We have to colour the item background for each column separately
    # So it is better to move this functionality in the subsequent for loop.
else:
    dc.SetTextForeground(colText)
```

**Patched code**:
```python
elif drawItemBackground:
    itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)
    dc.SetBrush(wx.Brush(colBg, wx.SOLID))
    dc.DrawRectangle(itemrect)
    dc.SetTextForeground(colText)
else:
    dc.SetTextForeground(colText)
```

## How It Works

1. The venv is created with `--system-site-packages` to access system wxPython
2. The patched file is copied to `.venv/lib/python3.11/site-packages/wx/lib/agw/hypertreelist.py`
3. Python's import system finds the venv version first, using our patched file instead of the system one
4. No system files are modified

## Installation

Run the patch installation script from the repository root:

```bash
./apply-wxpython-patch.sh
```

This script:
1. Creates the necessary directory structure in the venv
2. Copies the patched file to the correct location
3. Verifies the patch was applied successfully

## Maintenance

To update this patch:

1. Get the original file from system: `/usr/lib/python3/dist-packages/wx/lib/agw/hypertreelist.py`
2. Apply the changes shown above
3. Save to `patches/wxpython/hypertreelist.py`
4. Run `./apply-wxpython-patch.sh` to update the venv

## References

- wxPython Issue #2081: TR_FULL_ROW_HIGHLIGHT broken in Phoenix 4.x
- wxPython Issue #1898: TR_FILL_WHOLE_COLUMN_BACKGROUND broken for right-aligned columns
- wxPython PR #2088: Fix for both issues (included in 4.2.4)
