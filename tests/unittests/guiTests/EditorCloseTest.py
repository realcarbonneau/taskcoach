# -*- coding: utf-8 -*-

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

"""
Tests for editor dialog close behavior, specifically testing for
crashes when closing dialogs quickly after opening (before GTK
layout completion).
"""

from taskcoachlib import gui, config, persistence, operating_system
from taskcoachlib.domain import task, date
import test
import wx


class EditorCloseTestCase(test.wxTestCase):
    """Test case for editor close behavior."""

    def setUp(self):
        super().setUp()
        task.Task.settings = self.settings = config.Settings(load=False)
        self.taskFile = persistence.TaskFile()
        self.taskList = self.taskFile.tasks()
        self.task = task.Task("Task to edit")
        self.taskList.append(self.task)

    def tearDown(self):
        # Process any pending events
        if operating_system.isGTK():
            wx.Yield()
        super().tearDown()
        self.taskFile.close()
        self.taskFile.stop()


class ImmediateCloseTest(EditorCloseTestCase):
    """Test closing editor immediately after creation."""

    def testCloseImmediately(self):
        """Close editor immediately after creation - should not crash."""
        editor = gui.dialog.editor.TaskEditor(
            self.frame,
            [self.task],
            self.settings,
            self.taskList,
            self.taskFile,
        )
        # Close immediately without waiting for initialization
        editor.Close()
        # Process pending events
        wx.Yield()
        # If we get here without segfault, test passes

    def testCloseViaCancel(self):
        """Close editor via cancel button - should not crash."""
        editor = gui.dialog.editor.TaskEditor(
            self.frame,
            [self.task],
            self.settings,
            self.taskList,
            self.taskFile,
        )
        # Simulate cancel button press
        editor.cancel()
        # Process pending events
        wx.Yield()
        # If we get here without segfault, test passes

    def testCloseAfterShortDelay(self):
        """Close editor after very short delay - should not crash."""
        editor = gui.dialog.editor.TaskEditor(
            self.frame,
            [self.task],
            self.settings,
            self.taskList,
            self.taskFile,
        )
        # Let one round of events process (but not all)
        wx.YieldIfNeeded()
        editor.Close()
        wx.Yield()
        # If we get here without segfault, test passes

    def testCloseAfterInitialization(self):
        """Close editor after full initialization - should not crash."""
        editor = gui.dialog.editor.TaskEditor(
            self.frame,
            [self.task],
            self.settings,
            self.taskList,
            self.taskFile,
        )
        # Let all pending events process (CallAfter etc)
        wx.Yield()
        # Now close
        editor.Close()
        wx.Yield()
        # If we get here without segfault, test passes

    def testMultipleRapidOpenClose(self):
        """Open and close multiple editors rapidly - should not crash."""
        for i in range(5):
            editor = gui.dialog.editor.TaskEditor(
                self.frame,
                [self.task],
                self.settings,
                self.taskList,
                self.taskFile,
            )
            editor.Close()
            wx.YieldIfNeeded()
        wx.Yield()
        # If we get here without segfault, test passes


class CategoryEditorCloseTest(EditorCloseTestCase):
    """Test closing category editor immediately."""

    def setUp(self):
        super().setUp()
        from taskcoachlib.domain import category
        self.category = category.Category("Test Category")
        self.taskFile.categories().append(self.category)

    def testCloseImmediately(self):
        """Close category editor immediately - should not crash."""
        editor = gui.dialog.editor.CategoryEditor(
            self.frame,
            [self.category],
            self.settings,
            self.taskFile.categories(),
            self.taskFile,
        )
        editor.Close()
        wx.Yield()
        # If we get here without segfault, test passes


if __name__ == '__main__':
    import unittest
    unittest.main()
