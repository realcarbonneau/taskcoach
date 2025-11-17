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
        interior_min_size = self._interior.GetMinSize()
        print(f"[Dialog.__init__] Interior min size after creation: {interior_min_size}")
        self._interior.SetSizerProps(expand=True, proportion=1)
        self.fillInterior()
        interior_min_size_after = self._interior.GetMinSize()
        print(f"[Dialog.__init__] Interior min size after fillInterior: {interior_min_size_after}")
        self._buttons = self.createButtons()
        self._panel.Fit()
        panel_size = self._panel.GetSize()
        print(f"[Dialog.__init__] Panel size after Fit: {panel_size}")
        self.Fit()
        dialog_size = self.GetSize()
        print(f"[Dialog.__init__] Dialog size after Fit: {dialog_size}")
        self.CentreOnParent()
        if not operating_system.isGTK():
            wx.CallAfter(self.Raise)
        wx.CallAfter(self._panel.SetFocus)

        # Bind resize event for live logging
        self.Bind(wx.EVT_SIZE, self.onResize)

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

    def onResize(self, event):
        """Log dialog and interior (notebook) sizes during resize."""
        event.Skip()  # Let the event propagate

        # Safety check - window might be closing
        if not self or not self._interior or not self._panel:
            return

        try:
            dialog_size = self.GetSize()
            interior_size = self._interior.GetSize()
            interior_min_size = self._interior.GetMinSize()
            panel_size = self._panel.GetSize()

            # Get editor type if available
            editor_type = getattr(self._interior, '__class__', type(self._interior)).__name__

            # Also log current page size if this is a notebook editor
            page_info = ""
            if hasattr(self._interior, 'GetSelection'):
                try:
                    sel = self._interior.GetSelection()
                    if sel >= 0:
                        page = self._interior.GetPage(sel)
                        if page:  # Safety check
                            page_size = page.GetSize()
                            page_name = getattr(page, 'pageName', 'unknown')
                            page_info = f", CurrentPage({page_name}): {page_size}"
                except:
                    pass

            print(f"[RESIZE {editor_type}] Dialog: {dialog_size}, Interior: {interior_size}, Interior MinSize: {interior_min_size}, Panel: {panel_size}{page_info}")
        except:
            # Silently ignore errors during logging (window might be closing)
            pass

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
    def __init__(self, title, htmlText, *args, **kwargs):
        self._htmlText = htmlText
        super().__init__(None, title, buttonTypes=wx.ID_CLOSE, *args, **kwargs)

    def createInterior(self):
        interior = HtmlWindowThatUsesWebBrowserForExternalLinks(
            self._panel, -1, size=(550, 400)
        )
        if self._direction:
            interior.SetLayoutDirection(self._direction)
        return interior

    def fillInterior(self):
        self._interior.AppendToPage(self._htmlText)

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
