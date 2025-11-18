#!/usr/bin/env python3
"""
Test script to reproduce the quick-close crash.

Run this script to test closing dialogs quickly.
It will open Edit Task dialogs and close them immediately,
logging timing information to help diagnose the crash.

Usage:
    python3 test_quick_close.py
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import wx
import time
from taskcoachlib import persistence, config
from taskcoachlib.domain import task, category
from taskcoachlib.gui.dialog import editor

class TestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Quick Close Test")

        # Create minimal required objects
        self.settings = config.Settings(load=False)
        self.task_file = persistence.TaskFile()

        # Create a test task
        self.test_task = task.Task(subject="Test Task")
        self.task_file.tasks().append(self.test_task)

        # UI
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer.Add(self.log, 1, wx.EXPAND | wx.ALL, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn1 = wx.Button(panel, label="Test Quick Close (0ms)")
        btn1.Bind(wx.EVT_BUTTON, lambda e: self.test_close(0))
        btn_sizer.Add(btn1, 0, wx.ALL, 5)

        btn2 = wx.Button(panel, label="Test Close (50ms)")
        btn2.Bind(wx.EVT_BUTTON, lambda e: self.test_close(50))
        btn_sizer.Add(btn2, 0, wx.ALL, 5)

        btn3 = wx.Button(panel, label="Test Close (100ms)")
        btn3.Bind(wx.EVT_BUTTON, lambda e: self.test_close(100))
        btn_sizer.Add(btn3, 0, wx.ALL, 5)

        btn4 = wx.Button(panel, label="Test Close (500ms)")
        btn4.Bind(wx.EVT_BUTTON, lambda e: self.test_close(500))
        btn_sizer.Add(btn4, 0, wx.ALL, 5)

        sizer.Add(btn_sizer, 0, wx.CENTER)

        btn_batch = wx.Button(panel, label="Run Batch Test (10 iterations)")
        btn_batch.Bind(wx.EVT_BUTTON, self.batch_test)
        sizer.Add(btn_batch, 0, wx.CENTER | wx.ALL, 10)

        panel.SetSizer(sizer)
        self.SetSize(600, 400)
        self.Centre()

        self.log_message("Quick Close Test Ready")
        self.log_message("Click a button to test dialog close timing")
        self.log_message("")

    def log_message(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log.AppendText(f"[{timestamp}] {msg}\n")

    def test_close(self, delay_ms):
        """Open and close a TaskEditor with specified delay."""
        self.log_message(f"Opening TaskEditor...")
        start = time.time()

        try:
            dialog = editor.TaskEditor(
                self,
                [self.test_task],
                self.settings,
                self.task_file.tasks(),
                self.task_file
            )
            dialog.Show()

            open_time = (time.time() - start) * 1000
            self.log_message(f"  Dialog opened in {open_time:.1f}ms")

            if delay_ms > 0:
                self.log_message(f"  Waiting {delay_ms}ms before close...")
                wx.MilliSleep(delay_ms)

            # Close the dialog
            close_start = time.time()
            dialog.Close()
            close_time = (time.time() - close_start) * 1000

            self.log_message(f"  Close() returned in {close_time:.1f}ms")
            self.log_message(f"  SUCCESS - No crash with {delay_ms}ms delay")

        except Exception as e:
            self.log_message(f"  ERROR: {e}")

        self.log_message("")

    def batch_test(self, event):
        """Run multiple quick-close tests."""
        self.log_message("=" * 40)
        self.log_message("BATCH TEST: 10 iterations with 0ms delay")
        self.log_message("=" * 40)

        for i in range(10):
            self.log_message(f"Iteration {i+1}/10:")
            self.test_close(0)
            # Process events between iterations
            wx.GetApp().Yield()

        self.log_message("BATCH TEST COMPLETE")
        self.log_message("If you see this, no crashes occurred!")


class TestApp(wx.App):
    def OnInit(self):
        frame = TestFrame()
        frame.Show()
        return True


if __name__ == "__main__":
    print("Starting Quick Close Test...")
    print("This will help diagnose the dialog crash issue.")
    print("")

    app = TestApp()
    app.MainLoop()
