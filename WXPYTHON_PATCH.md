# wxPython Background Coloring Patch

## Quick Fix for Background Coloring Issues

Instead of upgrading to wxPython 4.2.4 (which requires compiling from source), you can patch the installed wxPython library directly. This is the **recommended solution** until Debian Bookworm packages are updated.

## What This Patch Fixes

- ✓ Full-row background colors (not just text backgrounds)
- ✓ Right-aligned columns (date columns) now have full cell backgrounds
- ✓ Background colors span the complete window width
- ✓ No white gaps between colored cells

## Automatic Patch Application

Run the provided patch script:

```bash
sudo ./patch-wxpython.sh
```

This will:
1. Locate your wxPython installation
2. Backup the original file
3. Apply the patch
4. Verify the patch was applied successfully

## Manual Patch Application

If you prefer to apply the patch manually:

### 1. Find the wxPython library location

```bash
python3 -c "import wx.lib.agw; print(wx.lib.agw.__path__[0])"
```

Typical location: `/usr/lib/python3/dist-packages/wx/lib/agw/`

### 2. Backup the original file

```bash
sudo cp /usr/lib/python3/dist-packages/wx/lib/agw/hypertreelist.py \
        /usr/lib/python3/dist-packages/wx/lib/agw/hypertreelist.py.backup
```

### 3. Edit the file

```bash
sudo nano /usr/lib/python3/dist-packages/wx/lib/agw/hypertreelist.py
```

### 4. Find the code to patch

Search for line ~3011, which contains:

```python
            elif drawItemBackground:

                pass
                # We have to colour the item background for each column separately
                # So it is better to move this functionality in the subsequent for loop.

            else:
                dc.SetTextForeground(colText)
```

### 5. Replace with the patched code

Replace the above section with:

```python
            elif drawItemBackground:
                itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)
                dc.SetBrush(wx.Brush(colBg, wx.SOLID))
                dc.DrawRectangle(itemrect)
                dc.SetTextForeground(colText)
            else:
                dc.SetTextForeground(colText)
```

### 6. Save and test

Save the file and run Task Coach to verify the fix works.

## What the Patch Does

The original wxPython 4.2.1 code had a `pass` statement that skipped drawing the background for full-row highlighting. The comment indicated it should be handled per-column, but this didn't work correctly.

The patch:
1. Creates a rectangle spanning the full row width (`total_w`)
2. Sets the brush to use the background color (`colBg`)
3. Draws the rectangle to fill the entire row background
4. Sets the text foreground color

This matches the behavior in wxPython 4.2.4 (PR #2088).

## Verifying the Patch

After applying the patch:

1. Launch Task Coach: `python3 taskcoach.py`
2. Create a category with a background color (e.g., light blue)
3. Create tasks in that category
4. Verify that:
   - ✓ All columns have full-width colored backgrounds
   - ✓ Date columns (right-aligned) show full cell background
   - ✓ No white gaps between columns
   - ✓ Colors span the complete window width

## Restoring the Original

If you need to restore the original wxPython file:

```bash
sudo cp /usr/lib/python3/dist-packages/wx/lib/agw/hypertreelist.py.backup \
        /usr/lib/python3/dist-packages/wx/lib/agw/hypertreelist.py
```

## Compatibility

This patch is:
- ✓ Safe to apply (only affects background rendering)
- ✓ Compatible with wxPython 4.2.1
- ✓ Based on the official fix in wxPython 4.2.4
- ✓ Will be overwritten if you upgrade wxPython (which is fine, as 4.2.4+ includes the fix)

## Alternative: Upgrade to wxPython 4.2.4

If you prefer to upgrade wxPython instead of patching, see `WXPYTHON_UPGRADE.md` for detailed instructions.

Note: Upgrading requires compiling from source (15-30 minutes) and installing GTK development libraries.

## References

- wxPython Issue #2081: TR_FULL_ROW_HIGHLIGHT broken in Phoenix 4.x
- wxPython Issue #1898: TR_FILL_WHOLE_COLUMN_BACKGROUND broken for right-aligned columns
- wxPython PR #2088: Fix for both issues (included in 4.2.4)
- Patch location: `/usr/lib/python3/dist-packages/wx/lib/agw/hypertreelist.py` line ~3011
