#!/usr/bin/env python3
"""
Test script to find the best approach for icon dropdowns in wxPython.

This tests different implementations to find one that works correctly
on GTK/Linux without the scroll position bug.

Run with: python test_icon_dropdown.py
"""

import wx
import wx.adv


class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Icon Dropdown Test", size=(600, 400))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Generate test items (80+ to trigger the scroll issue)
        self.items = [(f"icon_{i}", f"Item {i} - Test Label") for i in range(85)]

        # Test 1: Standard BitmapComboBox
        sizer.Add(wx.StaticText(panel, label="Test 1: BitmapComboBox (current approach)"),
                  flag=wx.ALL, border=5)
        self.combo1 = self._create_bitmap_combobox(panel)
        sizer.Add(self.combo1, flag=wx.ALL | wx.EXPAND, border=5)

        # Test 2: wx.Choice (no icons, for comparison)
        sizer.Add(wx.StaticText(panel, label="Test 2: wx.Choice (no icons, for comparison)"),
                  flag=wx.ALL, border=5)
        self.combo2 = wx.Choice(panel, choices=[item[1] for item in self.items])
        self.combo2.SetSelection(40)  # Select middle item
        sizer.Add(self.combo2, flag=wx.ALL | wx.EXPAND, border=5)

        # Test 3: wx.ComboBox with CB_READONLY
        sizer.Add(wx.StaticText(panel, label="Test 3: wx.ComboBox CB_READONLY"),
                  flag=wx.ALL, border=5)
        self.combo3 = wx.ComboBox(panel, choices=[item[1] for item in self.items],
                                   style=wx.CB_READONLY)
        self.combo3.SetSelection(40)
        sizer.Add(self.combo3, flag=wx.ALL | wx.EXPAND, border=5)

        # Test 4: OwnerDrawnComboBox (custom implementation)
        sizer.Add(wx.StaticText(panel, label="Test 4: OwnerDrawnComboBox (custom)"),
                  flag=wx.ALL, border=5)
        self.combo4 = IconOwnerDrawnComboBox(panel, self.items)
        self.combo4.SetSelection(40)
        sizer.Add(self.combo4, flag=wx.ALL | wx.EXPAND, border=5)

        # Test 5: ListBox in a popup (alternative approach)
        sizer.Add(wx.StaticText(panel, label="Test 5: Button + ListBox popup"),
                  flag=wx.ALL, border=5)
        self.combo5 = ListBoxDropdown(panel, self.items)
        sizer.Add(self.combo5, flag=wx.ALL | wx.EXPAND, border=5)

        panel.SetSizer(sizer)
        self.Centre()

    def _create_bitmap_combobox(self, parent):
        """Create a BitmapComboBox with test items."""
        combo = wx.adv.BitmapComboBox(parent, style=wx.CB_READONLY)

        # Create a simple colored bitmap for each item
        for i, (icon_name, label) in enumerate(self.items):
            bmp = self._create_color_bitmap(i)
            combo.Append(label, bmp)

        combo.SetSelection(40)  # Select middle item to trigger scroll
        return combo

    def _create_color_bitmap(self, index):
        """Create a simple colored bitmap for testing."""
        bmp = wx.Bitmap(16, 16)
        dc = wx.MemoryDC(bmp)

        # Create different colors based on index
        r = (index * 3) % 256
        g = (index * 7) % 256
        b = (index * 11) % 256
        dc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0)))
        dc.DrawRectangle(0, 0, 16, 16)

        dc.SelectObject(wx.NullBitmap)
        return bmp


class IconOwnerDrawnComboBox(wx.adv.OwnerDrawnComboBox):
    """Custom OwnerDrawnComboBox that draws icons."""

    def __init__(self, parent, items):
        super().__init__(parent, style=wx.CB_READONLY)
        self._items = items
        self._bitmaps = []

        for i, (icon_name, label) in enumerate(items):
            bmp = self._create_color_bitmap(i)
            self._bitmaps.append(bmp)
            self.Append(label)

    def _create_color_bitmap(self, index):
        """Create a simple colored bitmap for testing."""
        bmp = wx.Bitmap(16, 16)
        dc = wx.MemoryDC(bmp)
        r = (index * 3) % 256
        g = (index * 7) % 256
        b = (index * 11) % 256
        dc.SetBrush(wx.Brush(wx.Colour(r, g, b)))
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0)))
        dc.DrawRectangle(0, 0, 16, 16)
        dc.SelectObject(wx.NullBitmap)
        return bmp

    def OnDrawItem(self, dc, rect, item, flags):
        """Draw an item with icon and text."""
        if item == wx.NOT_FOUND:
            return

        # Draw bitmap
        if item < len(self._bitmaps):
            dc.DrawBitmap(self._bitmaps[item], rect.x + 2, rect.y + 2, True)

        # Draw text
        text = self.GetString(item)
        dc.DrawText(text, rect.x + 22, rect.y + 2)

    def OnMeasureItem(self, item):
        """Return height of item."""
        return 20

    def OnMeasureItemWidth(self, item):
        """Return width of item."""
        return -1  # Use default


class ListBoxDropdown(wx.Panel):
    """Alternative: Button that opens a ListBox popup."""

    def __init__(self, parent, items):
        super().__init__(parent)
        self._items = items
        self._selection = 40

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._text = wx.TextCtrl(self, style=wx.TE_READONLY)
        self._text.SetValue(items[self._selection][1])
        sizer.Add(self._text, proportion=1, flag=wx.EXPAND)

        self._button = wx.Button(self, label="v", size=(25, -1))
        self._button.Bind(wx.EVT_BUTTON, self._onDropdown)
        sizer.Add(self._button)

        self.SetSizer(sizer)

    def _onDropdown(self, event):
        """Show popup with listbox."""
        popup = ListBoxPopup(self, self._items, self._selection)

        # Position popup below the control
        pos = self.ClientToScreen(wx.Point(0, self.GetSize().height))
        popup.Position(pos, (0, 0))

        if popup.ShowModal() == wx.ID_OK:
            self._selection = popup.GetSelection()
            self._text.SetValue(self._items[self._selection][1])

        popup.Destroy()

    def GetSelection(self):
        return self._selection

    def SetSelection(self, sel):
        self._selection = sel
        self._text.SetValue(self._items[sel][1])


class ListBoxPopup(wx.Dialog):
    """Popup dialog with a listbox."""

    def __init__(self, parent, items, selection):
        super().__init__(parent, style=wx.BORDER_SIMPLE | wx.STAY_ON_TOP)

        self._listbox = wx.ListBox(self, choices=[item[1] for item in items],
                                    size=(300, 200))
        self._listbox.SetSelection(selection)
        self._listbox.EnsureVisible(selection)

        self._listbox.Bind(wx.EVT_LISTBOX_DCLICK, self._onSelect)
        self._listbox.Bind(wx.EVT_KEY_DOWN, self._onKeyDown)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._listbox, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()

        self._listbox.SetFocus()

    def _onSelect(self, event):
        self.EndModal(wx.ID_OK)

    def _onKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK)
        elif event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def GetSelection(self):
        return self._listbox.GetSelection()


if __name__ == "__main__":
    app = wx.App()
    frame = TestFrame()
    frame.Show()
    app.MainLoop()
