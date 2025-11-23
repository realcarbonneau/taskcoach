"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from taskcoachlib import operating_system
from taskcoachlib.i18n import _
from wx.lib.agw import aui
from . import notebook
import wx
import wx.adv
import wx.html
from wx.lib import sized_controls
import os
from ..tools import wxhelper


class Dialog(sized_controls.SizedDialog):
    def __init__(
        self, parent, title, bitmap="edit", direction=None, *args, **kwargs
    ):
        self._buttonTypes = kwargs.get("buttonTypes", wx.OK | wx.CANCEL)
        super().__init__(
            parent,
            -1,
            title,
            style=wx.DEFAULT_DIALOG_STYLE
            | wx.RESIZE_BORDER
            | wx.MAXIMIZE_BOX
            | wx.MINIMIZE_BOX,
        )
        self.SetIcon(
            wx.ArtProvider.GetIcon(bitmap, wx.ART_FRAME_ICON, (16, 16))
        )

        if operating_system.isWindows7_OrNewer():
            # Without this the window has no taskbar icon on Windows, and the focus comes back to the main
            # window instead of this one when returning to Task Coach through Alt+Tab. Which is probably not
            # what we want.
            import win32gui, win32con

            exStyle = win32gui.GetWindowLong(
                self.GetHandle(), win32con.GWL_EXSTYLE
            )
            win32gui.SetWindowLong(
                self.GetHandle(),
                win32con.GWL_EXSTYLE,
                exStyle | win32con.WS_EX_APPWINDOW,
            )

        self._panel = self.GetContentsPane()
        self._panel.SetSizerType("vertical")
        self._panel.SetSizerProps(expand=True, proportion=1)
        self._direction = direction
        self._interior = self.createInterior()
        self._interior.SetSizerProps(expand=True, proportion=1)
        self.fillInterior()
        self._buttons = self.createButtons()
        self._panel.Fit()
        self.Fit()
        self.CentreOnParent()
        if not operating_system.isGTK():
            wx.CallAfter(self.__safeRaise)
        wx.CallAfter(self.__safePanelSetFocus)

    def __safeRaise(self):
        """Safely raise window, guarding against deleted C++ objects."""
        try:
            if self:
                self.Raise()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def __safePanelSetFocus(self):
        """Safely set focus on panel, guarding against deleted C++ objects."""
        try:
            if self._panel:
                self._panel.SetFocus()
        except RuntimeError:
            # wrapped C/C++ object has been deleted
            pass

    def SetExtraStyle(self, exstyle):
        # SizedDialog's constructor calls this to set WS_EX_VALIDATE_RECURSIVELY. We don't need
        # it, it makes the dialog appear in about 7 seconds, and it makes switching focus
        # between two controls take up to 5 seconds.
        pass

    def createInterior(self):
        raise NotImplementedError

    def fillInterior(self):
        pass

    def createButtons(self):
        buttonTypes = (
            wx.OK if self._buttonTypes == wx.ID_CLOSE else self._buttonTypes
        )
        buttonSizer = self.CreateStdDialogButtonSizer(
            buttonTypes
        )  # type: wx.StdDialogButtonSizer
        if self._buttonTypes & wx.OK or self._buttonTypes & wx.ID_CLOSE:
            wxhelper.getButtonFromStdDialogButtonSizer(
                buttonSizer, wx.ID_OK
            ).Bind(wx.EVT_BUTTON, self.ok)
        if self._buttonTypes & wx.CANCEL:
            wxhelper.getButtonFromStdDialogButtonSizer(
                buttonSizer, wx.ID_CANCEL
            ).Bind(wx.EVT_BUTTON, self.cancel)
        if self._buttonTypes == wx.ID_CLOSE:
            wxhelper.getButtonFromStdDialogButtonSizer(
                buttonSizer, wx.ID_OK
            ).SetLabel(_("Close"))
        self.SetButtonSizer(buttonSizer)
        return buttonSizer

    def ok(self, event=None):
        if event:
            event.Skip()
        self.Close(True)
        self.Destroy()

    def cancel(self, event=None):
        if event:
            event.Skip()
        self.Close(True)
        self.Destroy()

    def disableOK(self):
        wxhelper.getButtonFromStdDialogButtonSizer(
            self._buttons, wx.ID_OK
        ).Disable()

    def enableOK(self):
        wxhelper.getButtonFromStdDialogButtonSizer(
            self._buttons, wx.ID_OK
        ).Enable()


class NotebookDialog(Dialog):
    def createInterior(self):
        return notebook.Notebook(
            self._panel,
            agwStyle=aui.AUI_NB_DEFAULT_STYLE
            & ~aui.AUI_NB_TAB_SPLIT
            & ~aui.AUI_NB_TAB_MOVE
            & ~aui.AUI_NB_DRAW_DND_TAB,
        )

    def fillInterior(self):
        self.addPages()

    def __getitem__(self, index):
        return self._interior[index]

    def ok(self, *args, **kwargs):
        self.okPages()
        super().ok(*args, **kwargs)

    def okPages(self, *args, **kwargs):
        for page in self._interior:
            page.ok(*args, **kwargs)

    def addPages(self):
        raise NotImplementedError


class HtmlWindowThatUsesWebBrowserForExternalLinks(wx.html.HtmlWindow):
    def OnLinkClicked(self, linkInfo):  # pylint: disable=W0221
        openedLinkInExternalBrowser = False
        if linkInfo.GetTarget() == "_blank":
            import webbrowser  # pylint: disable=W0404

            try:
                webbrowser.open(linkInfo.GetHref())
                openedLinkInExternalBrowser = True
            except webbrowser.Error:
                pass
        if not openedLinkInExternalBrowser:
            super(
                HtmlWindowThatUsesWebBrowserForExternalLinks, self
            ).OnLinkClicked(linkInfo)


class HTMLDialog(Dialog):
    def __init__(self, title, htmlText, parent=None, *args, **kwargs):
        self._htmlText = htmlText
        super().__init__(parent, title, buttonTypes=wx.ID_CLOSE, *args, **kwargs)

    def createInterior(self):
        # Create a panel to hold both HTML content and test dropdowns
        panel = wx.Panel(self._panel)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # HTML content
        html_window = HtmlWindowThatUsesWebBrowserForExternalLinks(
            panel, -1, size=(550, 350)
        )
        if self._direction:
            html_window.SetLayoutDirection(self._direction)
        self._html_window = html_window
        sizer.Add(html_window, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        # Test dropdowns section
        test_panel = wx.Panel(panel)
        test_sizer = wx.BoxSizer(wx.VERTICAL)

        test_sizer.Add(
            wx.StaticText(test_panel, label="--- Test Dropdowns (85 items, selection at 40) ---"),
            flag=wx.ALL, border=2
        )

        # Generate test items
        test_items = [(f"Item {i}", f"Test Item {i} - Label Text") for i in range(85)]

        # Test 1: BitmapComboBox
        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(wx.StaticText(test_panel, label="BitmapComboBox:"),
                 flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self._test_bitmap_combo = wx.adv.BitmapComboBox(test_panel, style=wx.CB_READONLY)
        for i, (name, label) in enumerate(test_items):
            bmp = self._create_test_bitmap(i)
            self._test_bitmap_combo.Append(label, bmp)
        self._test_bitmap_combo.SetSelection(40)
        row1.Add(self._test_bitmap_combo, proportion=1, flag=wx.EXPAND)
        test_sizer.Add(row1, flag=wx.EXPAND | wx.ALL, border=2)

        # Test 2: wx.Choice
        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(wx.StaticText(test_panel, label="wx.Choice:"),
                 flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self._test_choice = wx.Choice(test_panel, choices=[item[1] for item in test_items])
        self._test_choice.SetSelection(40)
        row2.Add(self._test_choice, proportion=1, flag=wx.EXPAND)
        test_sizer.Add(row2, flag=wx.EXPAND | wx.ALL, border=2)

        test_panel.SetSizer(test_sizer)
        sizer.Add(test_panel, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)

        panel.SetSizer(sizer)
        return panel

    def _create_test_bitmap(self, index):
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

    def fillInterior(self):
        self._html_window.AppendToPage(self._htmlText)

    def OnLinkClicked(self, linkInfo):
        pass


def AttachmentSelector(**callerKeywordArguments):
    kwargs = {
        "message": _("Add attachment"),
        "default_path": os.getcwd(),
        "wildcard": _("All files (*.*)|*"),
        "flags": wx.FD_OPEN,
    }
    kwargs.update(callerKeywordArguments)
    return wx.FileSelector(**kwargs)  # pylint: disable=W0142
