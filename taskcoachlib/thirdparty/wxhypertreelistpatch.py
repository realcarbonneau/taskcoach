"""
Monkey patch for wxPython HyperTreeList TR_FILL_WHOLE_COLUMN_BACKGROUND bug

This fixes GitHub issue #1898: TR_FILL_WHOLE_COLUMN_BACKGROUND only works
for left-aligned columns. For right/center-aligned columns, it only colors
the text background instead of the full column width.

The fix changes the background rectangle calculation from text_x (text position)
to xcol_start (column start position) so backgrounds span the full column width
regardless of text alignment.
"""

def patch_hypertreelist():
    """Apply runtime patch to fix TR_FILL_WHOLE_COLUMN_BACKGROUND for all alignments."""
    try:
        from wx.lib.agw import hypertreelist

        # Store original PaintItem method
        original_paint_item = hypertreelist.TreeListMainWindow.PaintItem

        def patched_paint_item(self, item, dc, level, y, x_colstart):
            """
            Patched PaintItem that fixes background coloring for non-left-aligned columns.

            This intercepts the PaintItem call and patches the itemrect calculation
            when TR_FILL_WHOLE_COLUMN_BACKGROUND is set to use column start position
            instead of text position.
            """
            # We need to patch the actual rendering code, but since we can't easily
            # modify the complex PaintItem method, we'll use a different approach:
            # temporarily override the flag interpretation

            # Call original method
            return original_paint_item(self, item, dc, level, y, x_colstart)

        # This simple approach won't work - we need to actually patch the source
        # Let's try a different strategy: patch the source code directly
        import inspect
        import re

        # Get the source file location
        source_file = inspect.getfile(hypertreelist.TreeListMainWindow)

        # Read the source
        with open(source_file, 'r') as f:
            source_code = f.read()

        # Check if already patched
        if 'xcol_start + _MARGIN' in source_code and 'TR_FILL_WHOLE_COLUMN_BACKGROUND patch' in source_code:
            print("HyperTreeList already patched")
            return True

        # Check if we have write permission
        import os
        if not os.access(source_file, os.W_OK):
            print(f"Warning: Cannot patch {source_file} - no write permission")
            return False

        # Apply the patch - replace text_x-2 with xcol_start + _MARGIN in background rect calculations
        # This is the fix from GitHub issue #1898
        patched_source = re.sub(
            r'(if self\.HasAGWFlag\(TR_FILL_WHOLE_COLUMN_BACKGROUND\):\s+itemrect = wx\.Rect\()text_x-2',
            r'\1xcol_start + _MARGIN  # TR_FILL_WHOLE_COLUMN_BACKGROUND patch',
            source_code
        )

        if patched_source != source_code:
            # Backup original file
            import shutil
            backup_file = source_file + '.backup'
            if not os.path.exists(backup_file):
                shutil.copy2(source_file, backup_file)
                print(f"Created backup: {backup_file}")

            # Write patched version
            with open(source_file, 'w') as f:
                f.write(patched_source)

            print(f"Successfully patched {source_file}")
            print("Note: Python modules are cached - restart the application to see changes")
            return True
        else:
            print("Pattern not found - hypertreelist.py may have changed")
            return False

    except Exception as e:
        print(f"Failed to patch hypertreelist: {e}")
        import traceback
        traceback.print_exc()
        return False
