# TaskCoach UI Framework Controls Comparison

This document compares wxPython controls used in TaskCoach with their equivalents in PySide6/PyQt6 and Tkinter.

## Executive Summary

| Framework | Suitable for TaskCoach? | Schedule Widget | Docking | License |
|-----------|------------------------|-----------------|---------|---------|
| **wxPython** | ✅ Current | ✅ wxScheduler | ✅ AUI | wxWindows (permissive) |
| **PySide6** | ✅ Best alternative | ❌ Must build | ✅ QtAds | LGPL (permissive) |
| **PyQt6** | ✅ Viable | ❌ Must build | ✅ QtAds | GPL or Commercial |
| **Tkinter** | ❌ No | ❌ None | ❌ None | PSF (permissive) |

---

## Tree/List Controls

| TaskCoach Widget | wxPython | PySide6/PyQt6 | Tkinter |
|------------------|----------|---------------|---------|
| Multi-column tree | `HyperTreeList` | `QTreeView` + `QStandardItemModel` | `ttk.Treeview` |
| Virtual list (large data) | `VirtualListCtrl` | `QListView` + lazy model | ❌ Manual only |
| Checkbox tree | `CheckTreeCtrl` | `QTreeView` + custom delegate | ⚠️ Hacky (images) |
| Checkbox list | `CheckListBox` | `QListWidget` + checkboxes | `ttk.Treeview` |

### Notes
- **PySide6 advantage**: Model/View architecture handles millions of rows efficiently
- **Tkinter limitation**: No built-in virtual mode for large datasets

---

## Calendar/Scheduling Controls

| TaskCoach Widget | wxPython | PySide6/PyQt6 | Tkinter |
|------------------|----------|---------------|---------|
| Month picker | `wx.adv.CalendarCtrl` | `QCalendarWidget` | ❌ (tkcalendar 3rd party) |
| **Week/Day scheduler** | ✅ `wxScheduler` | ❌ **None - must build** | ❌ None |
| Date/time input | Custom `DateTimeCtrl` | `QDateTimeEdit` | ❌ Manual |
| Time entry | Custom `TimeEntry` | `QTimeEdit` | ❌ Manual |

### The Scheduler Gap

**wxScheduler** provides Google Calendar-style week/day views with:
- Hourly time slots
- Drag-and-drop appointment scheduling
- Multi-day events
- Visual appointment blocks

**No equivalent exists in PyQt/PySide.** Options for migration:
1. Build custom widget using `QGraphicsView` (~2-4 weeks)
2. Port wxScheduler to Qt (~1-2 weeks)
3. Embed JavaScript scheduler via `QWebEngineView`

---

## Docking/Layout Controls

| TaskCoach Widget | wxPython | PySide6/PyQt6 | Tkinter |
|------------------|----------|---------------|---------|
| Docking framework | `AuiManager` | [Qt-Advanced-Docking-System](https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System) | ❌ None |
| Tabbed notebook | `AuiNotebook` | `QTabWidget` / `QDockWidget` | `ttk.Notebook` |
| Splitter panes | `wx.SplitterWindow` | `QSplitter` | `ttk.PanedWindow` |
| Toolbar | `AuiToolBar` | `QToolBar` | ❌ Basic frame |

### Notes
- **Qt-Advanced-Docking-System** is pip-installable: `pip install PySide6-QtAds`
- Provides full AUI-equivalent functionality

---

## Chart/Visualization Controls

| TaskCoach Widget | wxPython | PySide6/PyQt6 | Tkinter |
|------------------|----------|---------------|---------|
| Pie chart | `wx.lib.agw.piectrl` | `QtCharts.QPieSeries` | ❌ Canvas only |
| Timeline | Custom | `QGraphicsView` | ❌ Canvas only |
| Square map | Custom `TcSquareMap` | `QGraphicsView` | ❌ Canvas only |

### Notes
- **QtCharts** provides professional charting out of the box
- Tkinter requires manual Canvas drawing for any visualization

---

## Input Controls

| TaskCoach Widget | wxPython | PySide6/PyQt6 | Tkinter |
|------------------|----------|---------------|---------|
| Text input | `wx.TextCtrl` | `QLineEdit` / `QTextEdit` | `ttk.Entry` / `tk.Text` |
| Search box | `wx.SearchCtrl` | `QLineEdit` + actions | ❌ Manual |
| Spin control | `wx.SpinCtrl` | `QSpinBox` | `ttk.Spinbox` |
| Combo box | `wx.ComboBox` | `QComboBox` | `ttk.Combobox` |
| Combo tree | `ComboTreeBox` | ⚠️ Custom needed | ❌ None |
| Color picker | `wx.ColourDialog` | `QColorDialog` | `colorchooser` |
| Font picker | `wx.FontDialog` | `QFontDialog` | ❌ Manual |
| Slider | `wx.Slider` | `QSlider` | `ttk.Scale` |

---

## Dialog Controls

| TaskCoach Widget | wxPython | PySide6/PyQt6 | Tkinter |
|------------------|----------|---------------|---------|
| Standard dialog | `wx.Dialog` | `QDialog` | `tk.Toplevel` |
| File dialog | `wx.FileDialog` | `QFileDialog` | `filedialog` |
| Directory dialog | `wx.DirDialog` | `QFileDialog` | `filedialog` |
| Message box | `wx.MessageBox` | `QMessageBox` | `messagebox` |
| Progress dialog | `wx.ProgressDialog` | `QProgressDialog` | ⚠️ Manual |
| Wizard | `wx.adv.Wizard` | `QWizard` | ❌ Manual |

---

## HTML/Rich Content

| TaskCoach Widget | wxPython | PySide6/PyQt6 | Tkinter |
|------------------|----------|---------------|---------|
| HTML display | `wx.html.HtmlWindow` | `QTextBrowser` | ❌ Very limited |
| Web browser | `wx.html2.WebView` | `QWebEngineView` | ❌ None |
| Hyperlink | `HyperLinkCtrl` | `QLabel` with link | ⚠️ Manual |

---

## Drag and Drop

| Feature | wxPython | PySide6/PyQt6 | Tkinter |
|---------|----------|---------------|---------|
| File drop | `wx.FileDropTarget` | `QMimeData` | ⚠️ Limited |
| Text drop | `wx.TextDropTarget` | `QMimeData` | ⚠️ Limited |
| Custom data | `wx.CustomDataObject` | `QMimeData` | ❌ Basic |
| Tree item drag | ✅ Built-in | ✅ Built-in | ⚠️ Finicky |

---

## Printing

| Feature | wxPython | PySide6/PyQt6 | Tkinter |
|---------|----------|---------------|---------|
| Print dialog | `wx.PrintDialog` | `QPrintDialog` | ❌ None |
| Page setup | `wx.PageSetupDialog` | `QPageSetupDialog` | ❌ None |
| Print preview | `wx.PrintPreview` | `QPrintPreviewDialog` | ❌ None |
| Custom printout | `wx.Printout` | `QPrinter` + `QPainter` | ❌ None |

---

## Third-Party Components Used by TaskCoach

| Component | Description | PySide6 Equivalent |
|-----------|-------------|-------------------|
| `wxScheduler` | Week/day calendar view | ❌ Must build custom |
| `HyperTreeList` (patched) | Multi-column tree with full row highlight | `QTreeView` (native support) |
| `SmartDateTimeCtrl` | Intelligent date/time parsing | ⚠️ Custom needed |

---

## Coverage Summary

| Category | PySide6 Coverage | Tkinter Coverage |
|----------|------------------|------------------|
| Trees/Lists | ✅ 100% (better) | ⚠️ 70% (basic) |
| Calendar/Scheduling | ⚠️ 60% (no week view) | ❌ 20% |
| Docking | ✅ 100% (via QtAds) | ❌ 0% |
| Charts | ✅ 100% (QtCharts) | ❌ 0% |
| Input controls | ✅ 100% | ✅ 90% |
| Dialogs | ✅ 100% | ⚠️ 70% |
| Printing | ✅ 100% | ❌ 0% |
| **Overall** | **~95%** | **~40%** |

---

## Conclusion

### PySide6/PyQt6
- **Viable migration target** with excellent widget coverage
- **Main gap**: Week/day scheduler widget must be built custom
- **Recommendation**: Best alternative if migrating from wxPython

### Tkinter
- **Not suitable** for TaskCoach
- Missing critical features: docking, scheduler, charts, printing
- Only appropriate for simple applications

### wxPython
- **Current framework** - works well
- **Advantage**: wxScheduler is rare in Python ecosystem
- **Disadvantage**: Smaller community, requires patches for bugs

---

## References

- [Qt-Advanced-Docking-System](https://github.com/githubuser0xFFFF/Qt-Advanced-Docking-System)
- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- [wxPython Documentation](https://docs.wxpython.org/)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
