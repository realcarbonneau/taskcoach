#!/bin/bash

# Script to copy patched wxPython file to venv
# This applies the fix from wxPython PR #2088 for full-row background coloring

set -e

echo "=========================================="
echo "Applying wxPython Patch to venv"
echo "=========================================="
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "✗ ERROR: .venv directory not found"
    echo "  Please create the virtual environment first:"
    echo "  python3 -m venv --system-site-packages .venv"
    exit 1
fi

# Determine Python version
PYTHON_VERSION=$(.venv/bin/python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# Create target directory structure
TARGET_DIR=".venv/lib/python${PYTHON_VERSION}/site-packages/wx/lib/agw"
echo "Creating directory: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

# Copy patched file
SOURCE_FILE="patches/wxpython/hypertreelist.py"
TARGET_FILE="$TARGET_DIR/hypertreelist.py"

if [ ! -f "$SOURCE_FILE" ]; then
    echo "✗ ERROR: Patched file not found: $SOURCE_FILE"
    exit 1
fi

echo "Copying patched file..."
cp "$SOURCE_FILE" "$TARGET_FILE"

# Verify the patch
if grep -q "itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)" "$TARGET_FILE"; then
    echo "✓ Patch verified successfully!"
else
    echo "✗ WARNING: Could not verify patch in target file"
    exit 1
fi

echo ""
echo "=========================================="
echo "Patch Applied Successfully!"
echo "=========================================="
echo ""
echo "The patched wxPython file has been installed to:"
echo "  $TARGET_FILE"
echo ""
echo "This file will override the system wxPython when running"
echo "Task Coach from this venv, providing full-row background"
echo "coloring for all columns."
echo ""
echo "Next steps:"
echo "1. Run Task Coach: ./taskcoach-run.sh"
echo "2. Test background coloring on categories and tasks"
echo ""
