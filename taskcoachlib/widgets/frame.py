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
import time

# Startup logging for AUI pane operations
_startup_time = time.time()
_aui_log_enabled = True
_aui_update_count = 0
_aui_pane_add_count = 0


def _aui_log(msg):
    """Log AUI operations during startup to help diagnose flickering."""
    global _aui_update_count, _aui_pane_add_count
    if _aui_log_enabled:
        elapsed = time.time() - _startup_time
        print(f"[AUI {elapsed:.3f}s] {msg}")
        # Track counts for summary
        if "manager.Update" in msg or "After Update" in msg:
            _aui_update_count += 1
        if "addPane:" in msg:
            _aui_pane_add_count += 1


def disable_aui_startup_logging():
    """Call this after startup to disable verbose AUI logging."""
    global _aui_log_enabled
    if _aui_log_enabled:
        elapsed = time.time() - _startup_time
        print(f"\n[AUI {elapsed:.3f}s] ===== STARTUP SUMMARY =====")
        print(f"[AUI {elapsed:.3f}s] Total panes added: {_aui_pane_add_count}")
        print(f"[AUI {elapsed:.3f}s] Total manager.Update() calls: {_aui_update_count}")
        print(f"[AUI {elapsed:.3f}s] Each Update() causes a full layout recalculation")
        print(f"[AUI {elapsed:.3f}s] This explains the {_aui_pane_add_count + _aui_update_count} resize events during {elapsed:.2f}s startup")
        print(f"[AUI {elapsed:.3f}s] ===========================\n")
        _aui_log_enabled = False


class AuiManagedFrameWithDynamicCenterPane(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aui_log("AuiManagedFrameWithDynamicCenterPane.__init__ starting")
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
        self.bindEvents()
        _aui_log("AuiManagedFrameWithDynamicCenterPane.__init__ complete")

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
        is_center = not self.dockedPanes()
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
        if is_center:
            paneInfo = paneInfo.Center()
        self.manager.AddPane(window, paneInfo)
        _aui_log(f"addPane: name={name}, caption={caption}, floating={floating}, center={is_center}")
        self._log_all_pane_info("After AddPane")
        self.manager.Update()
        self._log_all_pane_info("After Update")

    def _log_all_pane_info(self, context):
        """Log current state of all panes for debugging startup flickering."""
        panes = self.manager.GetAllPanes()
        _aui_log(f"  {context}: {len(panes)} panes total")
        for pane in panes:
            if pane.IsToolbar():
                continue
            dock_dir = ["None", "Top", "Right", "Bottom", "Left", "Center"][
                min(pane.dock_direction_get(), 5)
            ]
            rect = pane.rect
            _aui_log(
                f"    - {pane.name}: dock={dock_dir}, "
                f"rect=({rect.x},{rect.y},{rect.width},{rect.height}), "
                f"shown={pane.IsShown()}, floating={pane.IsFloating()}"
            )

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
