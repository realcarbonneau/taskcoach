#!/usr/bin/env python3
"""
Minimal test case for AUI toolbar icon jitter during sash drag.

Toggle the flags below to isolate the root cause:
- USE_LIVE_RESIZE: Enable/disable live resize during sash drag
- USE_STRETCH_SPACER: Use stretch spacer vs fixed spacer
- ADD_ITEMS_AFTER_SPACER: Add items after the spacer
"""

VERSION = "1.2"

import wx
import wx.lib.agw.aui as aui

# === TOGGLE THESE TO TEST ===
USE_LIVE_RESIZE = True        # Try False - does jitter still happen?
USE_STRETCH_SPACER = True     # Try False - use AddSpacer instead
ADD_ITEMS_AFTER_SPACER = True # Try False - no items after spacer
# ============================


class TestPanel(wx.Panel):
    """A panel with a toolbar and some content."""

    def __init__(self, parent, name):
        super().__init__(parent)
        self.name = name

        # Create toolbar
        self.toolbar = aui.AuiToolBar(self, agwStyle=aui.AUI_TB_DEFAULT_STYLE)

        # Left icon
        self.toolbar.AddSimpleTool(
            wx.ID_ANY, "Left",
            wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, (16, 16)),
            "Left icon"
        )

        # Spacer
        if USE_STRETCH_SPACER:
            self.toolbar.AddStretchSpacer(1)
        else:
            self.toolbar.AddSpacer(50)  # Fixed 50px spacer

        if ADD_ITEMS_AFTER_SPACER:
            # Right-aligned control (TextCtrl)
            text_ctrl = wx.TextCtrl(self.toolbar, wx.ID_ANY, "Search", size=(100, -1))
            self.toolbar.AddControl(text_ctrl)

            # Right icon
            self.toolbar.AddSimpleTool(
                wx.ID_ANY, "Right",
                wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, (16, 16)),
                "Right icon"
            )

        self.toolbar.Realize()

        # Create content
        flags_info = f"LIVE_RESIZE={USE_LIVE_RESIZE}, STRETCH={USE_STRETCH_SPACER}, ITEMS_AFTER={ADD_ITEMS_AFTER_SPACER}"
        content = wx.TextCtrl(
            self, wx.ID_ANY,
            f"Content for {name}\n\n{flags_info}\n\nDrag the sash and observe toolbar icons.",
            style=wx.TE_MULTILINE
        )

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolbar, flag=wx.EXPAND)
        sizer.Add(content, proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)


class MainFrame(wx.Frame):
    """Main frame with AUI manager."""

    def __init__(self):
        super().__init__(None, title=f"AUI Toolbar Jitter Test v{VERSION}", size=(800, 600))

        # Build AUI manager flags
        agwStyle = aui.AUI_MGR_DEFAULT
        if USE_LIVE_RESIZE:
            agwStyle |= aui.AUI_MGR_LIVE_RESIZE

        self.manager = aui.AuiManager(self, agwStyle)

        # Create center panel
        center_panel = TestPanel(self, "Center")
        self.manager.AddPane(
            center_panel,
            aui.AuiPaneInfo().Name("center").Caption("Center Panel").Center().CloseButton(False)
        )

        # Create right panel
        right_panel = TestPanel(self, "Right")
        self.manager.AddPane(
            right_panel,
            aui.AuiPaneInfo().Name("right").Caption("Right Panel").Right().BestSize((250, -1))
        )

        self.manager.Update()

        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Print current settings
        print(f"Version {VERSION}: LIVE_RESIZE={USE_LIVE_RESIZE}, STRETCH_SPACER={USE_STRETCH_SPACER}, ITEMS_AFTER_SPACER={ADD_ITEMS_AFTER_SPACER}")

    def on_close(self, event):
        self.manager.UnInit()
        event.Skip()


class TestApp(wx.App):
    def OnInit(self):
        frame = MainFrame()
        frame.Show()
        return True


if __name__ == "__main__":
    app = TestApp()
    app.MainLoop()
