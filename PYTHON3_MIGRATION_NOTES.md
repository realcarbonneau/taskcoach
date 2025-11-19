# Python 3 Migration Technical Notes

This document captures technical issues, fixes, and refactorings discovered during the migration of Task Coach from Python 2 to Python 3.

## Table of Contents

1. [Widget Resizing Issues](#widget-resizing-issues)
2. [wx.Timer Crash During Window Destruction](#wxtimer-crash-during-window-destruction)
3. [wxPython Compatibility](#wxpython-compatibility)
4. [Known Issues](#known-issues)
5. [Future Work](#future-work)

---

## Widget Resizing Issues

### Problem Overview

**Date Fixed:** November 2025
**Affected Components:** Editor dialogs, Viewer panels, VirtualListCtrl widgets
**Root Cause:** Multiple layers of MinSize locking preventing widgets from shrinking after growing

### Symptoms

1. **Initial Layout Broken:** Widgets would appear squashed (~200x200px) on first render
2. **Stuck at Large Sizes:** After expanding the effort viewer (which could grow to 3021px width), resizing the window smaller would not shrink the widgets back down
3. **Non-responsive UI:** Users could not resize editor dialogs to reasonable sizes

### Root Cause Analysis

The problem was caused by **4 separate layers** where wxPython's sizing system was locking MinSize values:

#### Layer 1: AuiNotebook Perspective (editor.py:1408)
```python
# BEFORE - Broken
self.LoadPerspective(perspective)

# AFTER - Fixed
# DISABLED: LoadPerspective was restoring stale AuiNotebook perspective with broken sizing
# self.LoadPerspective(perspective)
pass
```

**Why it failed:** `LoadPerspective()` was restoring a stale AuiNotebook perspective that contained broken sizing information from previous sessions.

#### Layer 2: Viewer.initLayout() (base.py:212)
```python
# BEFORE - Broken
self.SetSizerAndFit(self._sizer)

# AFTER - Fixed
self.SetSizer(self._sizer)  # Changed from SetSizerAndFit to prevent locking MinSize
```

**Why it failed:** `SetSizerAndFit()` was locking the Viewer's MinSize to the widget's current BestSize during initial layout.

#### Layer 3: BookPage.fit() (notebook.py:65)
```python
# BEFORE - Broken
self.SetSizerAndFit(self._sizer)

# AFTER - Fixed
self.SetSizer(self._sizer)  # Changed from SetSizerAndFit to prevent locking MinSize
```

**Why it failed:** `SetSizerAndFit()` was locking the BookPage's MinSize to its current size, affecting ALL widgets in the page including toolbar.

#### Layer 4: EditBook.addPages() (editor.py:1268-1270)
```python
# BEFORE - Broken
width, height = self.__get_minimum_page_size()
self.SetMinSize((width, self.GetHeightForPageHeight(height)))

# AFTER - Fixed
# DISABLED: SetMinSize was locking entire notebook to max page size
# width, height = self.__get_minimum_page_size()
# self.SetMinSize((width, self.GetHeightForPageHeight(height)))
```

**Why it failed:** EditBook was calculating `max(all page MinSizes)` and locking the entire notebook. When the Effort page had MinSize=3021px, the entire notebook was locked at 3021px width.

### Additional Fixes for GetEffectiveMinSize()

Even after removing the explicit `SetMinSize()` calls, widgets still wouldn't shrink because wxPython's `GetEffectiveMinSize()` returns `max(MinSize, BestSize)`. Two additional fixes were needed:

#### Fix 5: VirtualListCtrl.__init__() (listctrl.py:53)
```python
# Override GetEffectiveMinSize() which returns BestSize - allows sizer to shrink widget
self.SetMinSize((100, 50))
```

**Why needed:** Without this, `GetEffectiveMinSize()` would return the widget's BestSize (which could be 3021px), preventing the sizer from shrinking it.

#### Fix 6: Viewer.initLayout() (base.py:214)
```python
self.SetSizer(self._sizer)
# Prevent GetEffectiveMinSize() from returning child's BestSize
self.SetMinSize((100, 50))
```

**Why needed:** The Viewer panel itself needed a MinSize override to prevent `GetEffectiveMinSize()` from returning its child's BestSize. This allows the BookPage's GridBagSizer to properly resize the Viewer.

### Summary of All Fixes

| Fix | File | Line | Change | Reason |
|-----|------|------|--------|--------|
| 1 | editor.py | 1408 | Disabled `LoadPerspective()` | Stale perspective with broken sizing |
| 2 | base.py | 212 | `SetSizerAndFit()` → `SetSizer()` | Prevent locking Viewer MinSize |
| 3 | notebook.py | 65 | `SetSizerAndFit()` → `SetSizer()` | Prevent locking BookPage MinSize |
| 4 | editor.py | 1268-1270 | Disabled `SetMinSize()` | Prevent locking notebook to max page size |
| 5 | listctrl.py | 53 | Added `SetMinSize((100, 50))` | Override GetEffectiveMinSize() for widgets |
| 6 | base.py | 214 | Added `SetMinSize((100, 50))` | Override GetEffectiveMinSize() for Viewer panel |

### Key Learnings

1. **SetSizerAndFit() is dangerous:** In dynamic layouts, `SetSizerAndFit()` can lock MinSize values based on initial content, preventing future resizing.

2. **GetEffectiveMinSize() behavior:** wxPython returns `max(MinSize, BestSize)`, so even with no explicit MinSize, widgets can't shrink below their BestSize without setting a small MinSize override.

3. **Cascading size constraints:** Size constraints can cascade through multiple widget layers (Notebook → BookPage → Viewer → VirtualListCtrl). All layers must be fixed for resizing to work properly.

4. **AuiNotebook perspective persistence:** Perspective strings can become stale and carry broken sizing information across sessions.

### Testing Checklist

When working on sizing issues in the future, test:

- [ ] Initial dialog render (should not be squashed)
- [ ] Expand effort viewer with many columns
- [ ] Shrink window back to small size
- [ ] Switch between different editor tabs
- [ ] Close and reopen editor (persistence test)
- [ ] Multiple resize cycles (grow → shrink → grow → shrink)

---

## wx.Timer Crash During Window Destruction

### Problem Overview

**Date Fixed:** November 2025
**Affected Components:** Edit Task/Categories dialog, any viewer with SearchCtrl
**Root Cause:** wx.Timer firing after window destruction causes segfault

### Symptoms

1. **Crash on Quick Close:** Closing the Edit Task or Edit Categories dialog quickly (e.g., pressing ESC immediately after opening) causes a segmentation fault
2. **GTK-specific:** The crash primarily occurs on GTK/Linux platforms
3. **No Python Traceback:** The crash occurs in C++ code with no useful Python error message

### Root Cause Analysis

The crash was caused by the **SearchCtrl widget's timer** continuing to run after window destruction:

1. **SearchCtrl creates a timer** in `__init__` that delays search filtering (0.5 second delay)
2. **User closes dialog quickly** before timer fires
3. **Window is destroyed** but timer continues running
4. **Timer fires** and tries to call callback on destroyed objects
5. **Segfault occurs** in wxWidgets C++ code

This is a **known wxPython issue**:
- [Phoenix Issue #429](https://github.com/wxWidgets/Phoenix/issues/429): Timer causes hard crash during shutdown
- [Phoenix Issue #632](https://github.com/wxWidgets/Phoenix/issues/632): Crash if wx.Timer isn't stopped before window closes

### The Fix

#### 1. Add cleanup() method to SearchCtrl (searchctrl.py:157-161)

```python
def cleanup(self):
    """Stop the timer and clear callback to prevent crashes during window destruction."""
    if self.__timer.IsRunning():
        self.__timer.Stop()
    self.__callback = lambda *args, **kwargs: None  # Replace with no-op
```

#### 2. Call cleanup() in Search.unbind() (uicommand.py:2915-2919)

```python
def unbind(self, window, id_):
    self.__bound = False
    if hasattr(self, 'searchControl') and self.searchControl:
        self.searchControl.cleanup()
    super().unbind(window, id_)
```

### Why This Fixes the Issue

1. **Timer.Stop()** prevents the timer from firing after window destruction
2. **No-op callback** provides a fallback in case the timer fires before Stop() takes effect
3. **Called during unbind()** ensures cleanup happens during the normal widget teardown process

### Key Learnings

1. **wx.Timer must be explicitly stopped:** Unlike child windows, timers are not automatically stopped when their parent window is destroyed. The timer's "owner" is really just the target for events, not a true parent-child relationship.

2. **Callbacks hold references:** The timer's callback holds a reference to the Search UICommand, which holds a reference to the viewer, which prevents proper cleanup during destruction.

3. **GTK async cleanup:** GTK performs asynchronous cleanup that can crash if we destroy windows while timers are still running.

4. **This is a wxWidgets "wontfix":** The wxWidgets team considers this the application's responsibility, not a bug to fix in the framework.

### Pattern for Future Timer Usage

When using wx.Timer in wxPython, always:

```python
class MyWidget(wx.Window):
    def __init__(self, parent):
        super().__init__(parent)
        self.__timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.__timer)
        # ... timer.Start() somewhere

    def cleanup(self):
        """Call this before window destruction."""
        if self.__timer.IsRunning():
            self.__timer.Stop()

    # OR bind to EVT_WINDOW_DESTROY:
    def __init__(self, parent):
        # ...
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)

    def onDestroy(self, event):
        if self.__timer.IsRunning():
            self.__timer.Stop()
        event.Skip()
```

### Debugging Segfaults with Faulthandler

**Date Implemented:** November 2025

To help diagnose segfaults that occur in wxPython/GTK C++ code, we've enabled Python's `faulthandler` module in `taskcoach.py`:

```python
import faulthandler
faulthandler.enable()
```

**What this provides:**

- Python traceback on segfaults showing the exact Python code that was executing
- Stack trace for all Python threads at the time of the crash
- Output to stderr (visible in terminal when running from command line)

**How to use:**

1. Run Task Coach from terminal: `python taskcoach.py`
2. Reproduce the crash
3. Check terminal output for the faulthandler traceback
4. The traceback will show the Python call stack leading to the segfault

**Example output:**
```
Fatal Python error: Segmentation fault

Current thread 0x00007f8b4c7fe700 (most recent call first):
  File "/taskcoachlib/gui/dialog/editor.py", line 964, in close
  File "/taskcoachlib/widgets/searchctrl.py", line 166, in onFind
  ...
```

This makes it much easier to identify which timer, callback, or widget is causing crashes during window destruction.

### Testing Checklist

When working with wx.Timer in the future, test:

- [ ] Open dialog and close immediately with ESC
- [ ] Open dialog, type in search, close quickly before search executes
- [ ] Open dialog, wait for timer to fire, then close
- [ ] Rapid open/close cycles (10+ times quickly)
- [ ] Test on GTK/Linux (most prone to this issue)
- [ ] Check faulthandler output if crashes occur

---

## wxPython Compatibility

### wxPython 4.2.0 Issues

See [CRITICAL_WXPYTHON_PATCH.md](CRITICAL_WXPYTHON_PATCH.md) for details on the category row background coloring bug in wxPython 4.2.0 shipped with Debian Bookworm.

### Version Requirements

- **Minimum:** wxPython 4.2.1-unicode
- **Recommended:** wxPython 4.2.1 or higher
- **Debian Bookworm:** Requires patch (see CRITICAL_WXPYTHON_PATCH.md)

---

## Known Issues

### Pending Issues

*None currently documented. Add issues here as they are discovered.*

### Resolved Issues

- ✅ Widget resizing stuck at large sizes (November 2025)
- ✅ wxPython 4.2.0 category background coloring (Documented in CRITICAL_WXPYTHON_PATCH.md)
- ✅ wx.Timer crash when closing Edit Task/Categories quickly (November 2025)
- ✅ Hacky close delay patches removed after root cause fix (November 2025)

---

## Future Work

### Areas for Investigation

1. **AuiNotebook Perspective Management**
   - Consider removing perspective persistence entirely
   - Or implement perspective validation before restoring
   - Current solution: Perspective disabled for editor dialogs

2. **Size Constraint Architecture**
   - Review all uses of `SetSizerAndFit()` in codebase
   - Document where `SetMinSize()` is actually needed vs. harmful
   - Consider creating wrapper methods with safer defaults

3. **Python 3 String Handling**
   - Audit all string/unicode handling
   - Ensure consistent use of str vs bytes
   - Review file I/O encoding

4. **Deprecated wxPython APIs**
   - Review all wx.FONTSTYLE_* usage
   - Check for other deprecated constants/methods

---

## Contributing to This Document

When adding new technical notes:

1. Include the date the issue was discovered/fixed
2. Provide before/after code examples
3. Explain the root cause, not just the symptoms
4. Add testing checklists when applicable
5. Link to related issues/PRs when available

---

**Last Updated:** November 19, 2025
