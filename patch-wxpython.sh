#!/bin/bash

# Script to patch wxPython 4.2.1 for full-row background coloring
# This applies the fix from wxPython PR #2088 without requiring a full upgrade

set -e

echo "=========================================="
echo "Task Coach - wxPython Background Patch"
echo "=========================================="
echo ""
echo "This script will patch the installed wxPython library to fix"
echo "background coloring issues in Task Coach on Debian Bookworm."
echo ""

# Find wxPython installation
echo "Locating wxPython installation..."
WX_PATH=$(python3 -c "import wx.lib.agw; print(wx.lib.agw.__path__[0])" 2>/dev/null)

if [ -z "$WX_PATH" ]; then
    echo "✗ ERROR: Could not locate wxPython installation."
    echo "  Make sure wxPython is installed: pip3 install wxPython"
    exit 1
fi

HYPERTREE_FILE="${WX_PATH}/hypertreelist.py"
BACKUP_FILE="${HYPERTREE_FILE}.backup-$(date +%Y%m%d-%H%M%S)"

echo "Found wxPython at: $WX_PATH"
echo "Target file: $HYPERTREE_FILE"
echo ""

# Check if file exists
if [ ! -f "$HYPERTREE_FILE" ]; then
    echo "✗ ERROR: hypertreelist.py not found at expected location."
    echo "  Expected: $HYPERTREE_FILE"
    exit 1
fi

# Check if already patched
if grep -q "itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)" "$HYPERTREE_FILE"; then
    echo "✓ This file appears to already be patched!"
    echo ""
    read -p "Do you want to re-apply the patch anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting without changes."
        exit 0
    fi
fi

# Create backup
echo "Creating backup..."
cp "$HYPERTREE_FILE" "$BACKUP_FILE"
echo "Backup saved to: $BACKUP_FILE"
echo ""

# Apply patch
echo "Applying patch..."

# Create temporary patch file
PATCH_FILE=$(mktemp)
cat > "$PATCH_FILE" << 'EOF'
--- hypertreelist.py.orig
+++ hypertreelist.py
@@ -3008,11 +3008,10 @@
             # On GTK+ 2, drawing a 'normal' background is wrong for themes that
             # don't allow backgrounds to be customized. Not drawing the background,
             # except for custom item backgrounds, works for both kinds of theme.
             elif drawItemBackground:
-
-                pass
-                # We have to colour the item background for each column separately
-                # So it is better to move this functionality in the subsequent for loop.
-
+                itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)
+                dc.SetBrush(wx.Brush(colBg, wx.SOLID))
+                dc.DrawRectangle(itemrect)
+                dc.SetTextForeground(colText)
             else:
                 dc.SetTextForeground(colText)

EOF

# Use sed to apply the patch (more reliable than patch command which may not be installed)
python3 << 'PYTHON_EOF'
import re

# Read the file
with open("$HYPERTREE_FILE", 'r') as f:
    content = f.read()

# Define the pattern to match (with flexible whitespace)
old_pattern = r'''(\s*# On GTK\+ 2, drawing a 'normal' background is wrong for themes that\s*
\s*# don't allow backgrounds to be customized\. Not drawing the background,\s*
\s*# except for custom item backgrounds, works for both kinds of theme\.\s*
\s*elif drawItemBackground:\s*)
\s*pass\s*
\s*# We have to colour the item background for each column separately\s*
\s*# So it is better to move this functionality in the subsequent for loop\.\s*
(\s*else:\s*
\s*dc\.SetTextForeground\(colText\))'''

# Replacement text
replacement = r'''\1itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)
                dc.SetBrush(wx.Brush(colBg, wx.SOLID))
                dc.DrawRectangle(itemrect)
                dc.SetTextForeground(colText)
            \2'''

# Apply the replacement
new_content = re.sub(old_pattern, replacement, content, flags=re.MULTILINE)

if new_content == content:
    print("WARNING: Pattern not found. Trying manual replacement...")
    # Fallback: simple string replacement
    old_text = """            elif drawItemBackground:

                pass
                # We have to colour the item background for each column separately
                # So it is better to move this functionality in the subsequent for loop.

            else:
                dc.SetTextForeground(colText)"""

    new_text = """            elif drawItemBackground:
                itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)
                dc.SetBrush(wx.Brush(colBg, wx.SOLID))
                dc.DrawRectangle(itemrect)
                dc.SetTextForeground(colText)
            else:
                dc.SetTextForeground(colText)"""

    new_content = content.replace(old_text, new_text)

    if new_content == content:
        print("ERROR: Could not apply patch!")
        exit(1)

# Write the modified content
with open("$HYPERTREE_FILE", 'w') as f:
    f.write(new_content)

print("Patch applied successfully!")
PYTHON_EOF

PATCH_RESULT=$?

if [ $PATCH_RESULT -ne 0 ]; then
    echo ""
    echo "✗ ERROR: Failed to apply patch!"
    echo "  Restoring backup..."
    cp "$BACKUP_FILE" "$HYPERTREE_FILE"
    echo "  Original file restored."
    rm -f "$PATCH_FILE"
    exit 1
fi

rm -f "$PATCH_FILE"

# Verify the patch
echo ""
echo "Verifying patch..."
if grep -q "itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)" "$HYPERTREE_FILE"; then
    echo "✓ Patch verified successfully!"
else
    echo "✗ WARNING: Could not verify patch. Check the file manually."
    exit 1
fi

echo ""
echo "=========================================="
echo "Patch Complete!"
echo "=========================================="
echo ""
echo "Backup saved to:"
echo "  $BACKUP_FILE"
echo ""
echo "Next steps:"
echo "1. Run Task Coach: python3 taskcoach.py"
echo "2. Create a category with a background color"
echo "3. Verify that all columns show full-width backgrounds"
echo "4. Check that date columns have full cell coloring"
echo ""
echo "To restore the original file:"
echo "  sudo cp $BACKUP_FILE $HYPERTREE_FILE"
echo ""
