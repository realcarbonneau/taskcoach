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

import wx
import wx.lib.agw.aui as aui
from taskcoachlib import operating_system


class AuiManagedFrameWithDynamicCenterPane(wx.Frame):
    """A wx.Frame with AUI manager that handles proportional pane resizing.

    When the main window is resized, panes docked at the edges (left, right,
    top, bottom) are scaled proportionally to maintain their relative sizes.
    This prevents side panes from being pushed off-screen when the window
    is made smaller.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        agwStyle = aui.AUI_MGR_DEFAULT | aui.AUI_MGR_ALLOW_ACTIVE_PANE
        if not operating_system.isWindows():
            # With this style on Windows, you can't dock back floating frames
            agwStyle |= wx.lib.agw.aui.AUI_MGR_USE_NATIVE_MINIFRAMES
        self.manager = aui.AuiManager(self, agwStyle)
        self.manager.SetAutoNotebookStyle(
            aui.AUI_NB_TOP
            | aui.AUI_NB_CLOSE_BUTTON
            | aui.AUI_NB_SUB_NOTEBOOK
            | aui.AUI_NB_SCROLL_BUTTONS
        )
        # Track the last known client size for proportional resizing
        self._last_client_size = None
        self._proportional_resize_enabled = True
        self.bindEvents()

    def bindEvents(self):
        for eventType in aui.EVT_AUI_PANE_CLOSE, aui.EVT_AUI_PANE_FLOATING:
            self.manager.Bind(eventType, self.onPaneClosingOrFloating)

    def onPaneClosingOrFloating(self, event):
        pane = event.GetPane()
        dockedPanes = self.dockedPanes()
        if self.isCenterPane(pane) and len(dockedPanes) == 1:
            event.Veto()
        else:
            event.Skip()
            if self.isCenterPane(pane):
                if pane in dockedPanes:
                    dockedPanes.remove(pane)
                dockedPanes[0].Center()

    def addPane(self, window, caption, name, floating=False):
        x, y = 0, 0
        if self.GetTopLevelParent().IsShown():
            x, y = window.GetPosition()
            x, y = window.ClientToScreen(x, y)
        paneInfo = aui.AuiPaneInfo()
        paneInfo = (
            paneInfo.CloseButton(True)
            .Floatable(True)
            .Name(name)
            .Caption(caption)
            .Right()
            .FloatingSize((300, 200))
            .BestSize((200, 200))
            .FloatingPosition((x + 30, y + 30))
            .CaptionVisible()
            .MaximizeButton()
            .DestroyOnClose()
        )
        if floating:
            paneInfo.Float()
        if not self.dockedPanes():
            paneInfo = paneInfo.Center()
        self.manager.AddPane(window, paneInfo)
        self.manager.Update()

    def setPaneTitle(self, window, title):
        self.manager.GetPane(window).Caption(title)

    def dockedPanes(self):
        return [
            pane
            for pane in self.manager.GetAllPanes()
            if not pane.IsToolbar()
            and not pane.IsFloating()
            and not pane.IsNotebookPage()
        ]

    def float(self, window):
        self.manager.GetPane(window).Float()

    @staticmethod
    def isCenterPane(pane):
        return pane.dock_direction_get() == aui.AUI_DOCK_CENTER

    def handleProportionalResize(self, new_size):
        """Scale docked pane sizes proportionally when the window is resized.

        This ensures that panes docked at the edges (left, right, top, bottom)
        maintain their proportional sizes relative to the window, preventing
        them from being pushed off-screen when the window is made smaller.

        Args:
            new_size: The new client area size (wx.Size) of the window.
        """
        if not self._proportional_resize_enabled:
            return

        if self._last_client_size is None:
            # First resize event - just store the size
            self._last_client_size = new_size
            return

        old_width = self._last_client_size.GetWidth()
        old_height = self._last_client_size.GetHeight()
        new_width = new_size.GetWidth()
        new_height = new_size.GetHeight()

        # Avoid division by zero and handle minimal size changes
        if old_width < 50 or old_height < 50:
            self._last_client_size = new_size
            return

        # Calculate scale factors
        width_scale = new_width / old_width
        height_scale = new_height / old_height

        # Skip if the change is negligible (less than 1%)
        if abs(width_scale - 1.0) < 0.01 and abs(height_scale - 1.0) < 0.01:
            return

        panes_modified = False

        for pane in self.manager.GetAllPanes():
            # Skip floating panes, toolbars, notebook pages, and center pane
            if (pane.IsFloating() or pane.IsToolbar() or
                pane.IsNotebookPage() or self.isCenterPane(pane)):
                continue

            dock_direction = pane.dock_direction_get()

            # Get current pane size
            pane_size = pane.best_size
            if pane_size.GetWidth() <= 0 or pane_size.GetHeight() <= 0:
                # Try to get size from the window itself
                if pane.window:
                    pane_size = pane.window.GetSize()
                if pane_size.GetWidth() <= 0 or pane_size.GetHeight() <= 0:
                    continue

            new_pane_width = pane_size.GetWidth()
            new_pane_height = pane_size.GetHeight()

            # Scale based on dock direction
            # Left/Right docked panes: scale width with window width
            # Top/Bottom docked panes: scale height with window height
            if dock_direction in (aui.AUI_DOCK_LEFT, aui.AUI_DOCK_RIGHT):
                new_pane_width = int(pane_size.GetWidth() * width_scale)
                # Ensure minimum size
                new_pane_width = max(new_pane_width, 50)
            elif dock_direction in (aui.AUI_DOCK_TOP, aui.AUI_DOCK_BOTTOM):
                new_pane_height = int(pane_size.GetHeight() * height_scale)
                # Ensure minimum size
                new_pane_height = max(new_pane_height, 50)

            if (new_pane_width != pane_size.GetWidth() or
                new_pane_height != pane_size.GetHeight()):
                new_size_obj = wx.Size(new_pane_width, new_pane_height)
                pane.BestSize(new_size_obj)
                if pane.window:
                    pane.window.SetSize(new_size_obj)
                panes_modified = True

        if panes_modified:
            self.manager.Update()

        self._last_client_size = new_size

    def initProportionalResize(self):
        """Initialize the proportional resize tracking with the current size.

        Call this after the window is fully laid out (e.g., after
        LoadPerspective) to establish the baseline size for proportional
        calculations.
        """
        self._last_client_size = self.GetClientSize()
