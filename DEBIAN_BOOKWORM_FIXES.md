# Debian Bookworm (Python 3) Compatibility Fixes

This document summarizes the fixes applied to make Task Coach work properly on Debian Bookworm with Python 3 and wxPython Phoenix 4.x.

## Summary of Issues Fixed

### 1. Icon Transparency ✓ FIXED

**Problem**: Toolbar icons (e.g., "Hide Completed Task", "Hide inactive tasks") had dark grey backgrounds instead of transparency.

**Root Cause**: Two issues in icon processing:
1. `taskcoachlib/tools/wxhelper.py:clearAlphaDataOfImage()` was using `np.frombuffer()` which creates a read-only numpy array
2. `taskcoachlib/gui/artprovider.py:CreateBitmap()` was clearing alpha channel to 255 (fully opaque)

**Fix**:
- `wxhelper.py`: Use `np.full()` to create a writable array
- `artprovider.py`: Preserve original icon's alpha channel when compositing overlays

**Files Modified**:
- `taskcoachlib/tools/wxhelper.py` (lines 69-78)
- `taskcoachlib/gui/artprovider.py` (lines 57-105)

### 2. Version Logging ✓ FIXED

**Problem**: No easy way to verify which version is running during development/debugging.

**Solution**: Added version logging at application startup showing version number and git commit count.

**Implementation**:
- Added `get_git_info()` function to get git commit count and hash
- Modified startup to print: `Task Coach 1.5.1.XXX (commit XXXXXXX)`

**Files Modified**:
- `taskcoachlib/meta/data.py` (lines 32-51)
- `taskcoachlib/application/application.py` (lines 210-217)

### 3. Category/Task Background Coloring ⚠️ PARTIALLY FIXED

**Problem**: Background colors didn't span the complete row width like they did in Python 2/wxPython 2.8.

**Root Cause**: Multiple wxPython Phoenix 4.x bugs:
1. Color tuples not automatically converted to wx.Colour objects in Python 3
2. `TR_FULL_ROW_HIGHLIGHT` broken (issue #2081) - only colors text backgrounds
3. `TR_FILL_WHOLE_COLUMN_BACKGROUND` broken for right-aligned columns (issue #1898)

**Fixes Applied**:

#### a) Explicit wx.Colour Conversion ✓
```python
bg_color = wx.Colour(*bg_color_tuple) if isinstance(bg_color_tuple, tuple) else bg_color_tuple
```

#### b) Loop Through All Columns ✓
```python
for column_index in range(self.GetColumnCount()):
    self.SetItemBackgroundColour(item, bg_color, column_index)
```

#### c) Remove White Gaps Between Columns ✓
```python
agw_style &= ~hypertreelist.TR_COLUMN_LINES
```

#### d) Enable Full Column Width Flag ✓
```python
agw_style |= hypertreelist.TR_FILL_WHOLE_COLUMN_BACKGROUND
```

**Current State with wxPython 4.2.1**:
- ✓ Left-aligned columns (Subject, etc.): Full cell background coloring
- ✓ No white gaps between columns
- ✗ Right-aligned columns (date columns): Only text background colored

**Final Fix Available**: Patch wxPython or upgrade to version 4.2.4
- **Option 1 (Recommended)**: Patch the installed wxPython library (see `WXPYTHON_PATCH.md`)
  - Quick: Takes less than 1 minute
  - Status: ✓ Already applied to this development environment
  - For deployment: Run `sudo python3 patch-wxpython-simple.py` (sudo needed for venv with --system-site-packages)
  - Safe: Creates automatic backup before patching
- **Option 2 (Alternative)**: Upgrade to wxPython 4.2.4 (see `WXPYTHON_UPGRADE.md`)
  - Requires compiling from source (15-30 minutes)
  - Requires GTK development libraries
  - Provides official fix from PR #2088

**Files Modified**:
- `taskcoachlib/widgets/treectrl.py` (lines 342-370, 477-492)
- `taskcoachlib/widgets/listctrl.py` (lines 103-124)

## Technical Details

### wxPython Phoenix vs Classic Differences

**Color Handling**:
- Classic (2.8): Automatically converted `(r, g, b)` tuples to `wx.Colour`
- Phoenix (4.x): Requires explicit `wx.Colour(*tuple)` conversion

**HyperTreeList Rendering**:
- Classic: `TR_FULL_ROW_HIGHLIGHT` painted full row backgrounds
- Phoenix 4.2.1: `TR_FULL_ROW_HIGHLIGHT` only paints text backgrounds (bug #2081)
- Phoenix 4.2.4: Fixed in PR #2088

**Column Alignment**:
- Left-aligned columns: `TR_FILL_WHOLE_COLUMN_BACKGROUND` works correctly
- Right-aligned columns: Broken in Phoenix 4.2.1, fixed in 4.2.4

### Affected Columns

**Left-aligned** (working properly):
- Subject/Task name
- Categories
- Notes
- Priority
- Budget
- Time spent
- Budget left
- Total budget
- Total time spent
- Total budget left

**Right-aligned** (requires wxPython 4.2.4):
- Planned start date
- Due date
- Actual start date
- Completion date

All date columns use `wx.LIST_FORMAT_RIGHT` alignment, which triggers the background coloring bug in wxPython 4.2.1.

## Commits

The following commits were made to address these issues:

```
1b9af7e Add automated wxPython 4.2.4 upgrade script
f5ec996 Document wxPython 4.2.4 upgrade requirement for full background coloring
f3d244d WORKAROUND: TR_FULL_ROW_HIGHLIGHT broken in wxPython Phoenix 4.x
9eb1b6f Use SetItemBackgroundColour with column=0 to leverage TR_FULL_ROW_HIGHLIGHT
0dd7ef8 Add TR_FILL_WHOLE_COLUMN_BACKGROUND flag to fill full column width
75ab80a Set background color for ALL columns with explicit wx.Colour
a81d4a6 Use SetItemBackgroundColour with explicit wx.Colour conversion
```

## Testing

### Icon Transparency
1. Launch Task Coach
2. Check toolbar icons for transparency (no grey backgrounds)
3. Verify overlay icons maintain transparency

### Version Logging
1. Launch Task Coach
2. Check terminal output for version line: `Task Coach 1.5.1.XXX (commit XXXXXXX)`

### Background Coloring (with wxPython 4.2.1)
1. Create a category with a background color
2. Create tasks in that category
3. Verify:
   - ✓ Subject column has full-width background color
   - ✓ No white gaps between columns
   - ⚠️ Date columns only have text background colored (expected limitation)

### Background Coloring (after wxPython 4.2.4 upgrade)
1. Run `./upgrade-wxpython.sh`
2. Launch Task Coach
3. Verify:
   - ✓ ALL columns have full-width background color
   - ✓ Date columns have full cell background (not just text)
   - ✓ No white gaps between columns
   - ✓ Colors match selection highlighting width

## Next Steps

1. **wxPython Patch Status**
   - ✓ **Already applied** to this development environment
   - Background coloring should now work correctly on all columns

   For deployment to other systems:
   - **Apply wxPython patch** (see `WXPYTHON_PATCH.md`) - **RECOMMENDED**
     - Quick and simple: `sudo python3 patch-wxpython-simple.py`
     - Alternatively: `sudo ./patch-wxpython.sh`
     - Note: sudo required for venvs using --system-site-packages
     - This patches your installed wxPython library with the fix from PR #2088

   **OR**

   - **Upgrade wxPython to 4.2.4** (see `WXPYTHON_UPGRADE.md`) - **ALTERNATIVE**
     - Option A: Run `./upgrade-wxpython.sh`
     - Option B: Manual upgrade with instructions in documentation
     - Note: Requires compiling from source (15-30 minutes)

2. **Test background coloring** to verify all columns work correctly
   - Create categories with background colors
   - Verify date columns (right-aligned) show full cell backgrounds

3. **Keep workarounds in code** for compatibility
   - The column loop workaround ensures compatibility with unpatched installations
   - The explicit wx.Colour conversion is required for Python 3/Phoenix compatibility
   - These workarounds do not interfere with the patch/upgrade

## References

- wxPython Issue #2081: https://github.com/wxWidgets/Phoenix/issues/2081
- wxPython Issue #1898: https://github.com/wxWidgets/Phoenix/issues/1898
- wxPython PR #2088: https://github.com/wxWidgets/Phoenix/pull/2088
- wxPython 4.2.4 Release: October 28, 2025

## Related Documentation

- `WXPYTHON_UPGRADE.md`: Detailed wxPython upgrade guide
- `upgrade-wxpython.sh`: Automated upgrade script
