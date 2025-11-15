# wxPython 4.2.4 Upgrade Required for Full Background Coloring

## Current Issue

With wxPython 4.2.1, the category and task background coloring has the following limitations:

1. **Left-aligned columns** (e.g., Subject/Task name): Full cell background coloring works correctly
2. **Right-aligned columns** (e.g., date columns): Only text background is colored, not the full cell width
3. **White gaps between columns**: Visible separation between colored cells

## Root Cause

wxPython Phoenix 4.x has two bugs affecting background coloring:

1. **Issue #2081**: `TR_FULL_ROW_HIGHLIGHT` only colors text backgrounds instead of full row
   - Workaround implemented: Loop through all columns and set background individually

2. **Issue #1898**: `TR_FILL_WHOLE_COLUMN_BACKGROUND` doesn't work with right-aligned columns
   - Affects date columns: Planned start date, Due date, Actual start date, Completion date
   - These columns use `wx.LIST_FORMAT_RIGHT` alignment
   - **No code workaround available** - requires wxPython upgrade

## Solution: Upgrade to wxPython 4.2.4

Both bugs were fixed in **PR #2088**, which is included in **wxPython 4.2.4** (released October 28, 2025).

### Upgrade Instructions

#### Method 1: Using pip (Recommended)

First, install required build dependencies:

```bash
sudo apt-get install -y \
    libgtk-3-dev \
    libnotify-dev \
    libsm-dev \
    libwebkit2gtk-4.0-dev \
    libjpeg-dev \
    libtiff-dev \
    libsdl2-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev
```

Then upgrade wxPython:

```bash
pip3 install --upgrade wxPython==4.2.4
```

**Note**: Building wxPython from source can take 15-30 minutes.

#### Method 2: Using pre-built wheels (if available for your platform)

Check if a pre-built wheel is available:

```bash
pip3 download wxPython==4.2.4 --only-binary :all:
```

If a wheel is found, install it:

```bash
pip3 install wxPython==4.2.4
```

### Verification

After upgrading, verify the version:

```bash
python3 -c "import wx; print(wx.version())"
```

Expected output: `4.2.4 gtk3 (phoenix) wxWidgets 3.2.4` (or similar)

### Expected Results

After upgrading to wxPython 4.2.4, you should see:

- Full-width background colors on **all** columns, including right-aligned date columns
- No white gaps between colored cells (with `TR_COLUMN_LINES` disabled)
- Consistent coloring across both the Category panel and Task panel
- Background colors matching the full width of selection highlighting

## Current Workarounds in Code

The following workarounds have been implemented in `taskcoachlib/widgets/treectrl.py`:

1. **Explicit wx.Colour conversion** for Python 3/Phoenix compatibility
2. **Loop through all columns** to set background on each column individually
3. **TR_COLUMN_LINES disabled** to remove white gaps between columns
4. **Both flags enabled**: `TR_FULL_ROW_HIGHLIGHT` + `TR_FILL_WHOLE_COLUMN_BACKGROUND`

These workarounds provide the best possible coloring with wxPython 4.2.1, but full functionality requires 4.2.4.

## Testing After Upgrade

1. Launch Task Coach: `python3 taskcoach.py`
2. Check version in startup log: Should show `Task Coach 1.5.1.XXX (commit ...)`
3. Create a category with a background color (e.g., light blue)
4. Create tasks in that category
5. Verify that:
   - All columns have full-width colored backgrounds
   - Date columns (right-aligned) show full cell background, not just text
   - No white gaps between columns
   - Colors match selection highlighting width

## References

- wxPython Issue #2081: https://github.com/wxWidgets/Phoenix/issues/2081
- wxPython Issue #1898: https://github.com/wxWidgets/Phoenix/issues/1898
- wxPython PR #2088: https://github.com/wxWidgets/Phoenix/pull/2088
- wxPython 4.2.4 Release: October 28, 2025
