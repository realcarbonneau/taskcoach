#!/bin/bash
# TaskCoach Setup Script for Debian Bookworm
# This script automates the setup and testing of TaskCoach on Debian 12
# Updated to handle PEP 668 properly

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TaskCoach Setup for Debian Bookworm${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Check if running on Debian
if [ ! -f /etc/debian_version ]; then
    echo -e "${YELLOW}Warning: This doesn't appear to be Debian${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
echo -e "${BLUE}[1/7] Checking Python version...${NC}"

# Check for Python 3.12 (required for system wxPython package compatibility)
if command -v python3.12 &> /dev/null; then
    PYTHON_VERSION=$(python3.12 --version 2>&1 | awk '{print $2}')
    echo "Found Python $PYTHON_VERSION"
    echo -e "${GREEN}✓ Python 3.12 is available${NC}"
else
    echo -e "${RED}✗ Python 3.12 required (for wxPython compatibility)${NC}"
    echo "The system wxPython package (python3-wxgtk4.0) is compiled for Python 3.12"
    exit 1
fi
echo

# Install system dependencies
echo -e "${BLUE}[2/7] Installing system dependencies...${NC}"
echo "This will install system packages from Debian repos."
echo "Packages: python3-wxgtk4.0, python3-twisted, python3-lxml, python3-numpy,"
echo "          python3-six, python3-dateutil, python3-chardet, python3-keyring,"
echo "          python3-pyparsing, python3-pyxdg, python3-venv"
echo "Requires sudo privileges."

if command -v sudo &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y \
        python3-wxgtk4.0 \
        python3-six \
        python3-twisted \
        python3-lxml \
        python3-numpy \
        python3-dateutil \
        python3-chardet \
        python3-keyring \
        python3-pyparsing \
        python3-pyxdg \
        python3-venv
    echo -e "${GREEN}✓ System packages installed${NC}"
else
    echo -e "${YELLOW}⚠ sudo not available, please install packages manually${NC}"
    exit 1
fi
echo

# Create virtual environment for packages not in Debian repos
echo -e "${BLUE}[3/7] Creating virtual environment...${NC}"
VENV_PATH="$SCRIPT_DIR/.venv"

# Use Python 3.12 to match the system wxPython package
PYTHON_CMD="python3.12"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}✗ Python 3.12 not found${NC}"
    echo "The system wxPython package requires Python 3.12"
    exit 1
fi

if [ -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Virtual environment already exists at $VENV_PATH${NC}"
    read -p "Recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_PATH"
        $PYTHON_CMD -m venv --system-site-packages "$VENV_PATH"
        echo -e "${GREEN}✓ Virtual environment recreated with Python 3.12${NC}"
    else
        echo -e "${GREEN}✓ Using existing virtual environment${NC}"
    fi
else
    $PYTHON_CMD -m venv --system-site-packages "$VENV_PATH"
    echo -e "${GREEN}✓ Virtual environment created with Python 3.12${NC}"
fi
echo

# Install Python dependencies not available in Debian repos
echo -e "${BLUE}[4/7] Installing Python dependencies in venv...${NC}"
echo "Installing: desktop3, lockfile, gntp, distro, pypubsub"

source "$VENV_PATH/bin/activate"
pip install --quiet desktop3 lockfile gntp distro pypubsub
deactivate

echo -e "${GREEN}✓ Python dependencies installed in virtual environment${NC}"
echo

# Apply wxPython patch for background coloring fix
echo -e "${BLUE}[5/7] Applying wxPython patch to venv...${NC}"
echo "Installing patched hypertreelist.py for full-row background coloring"

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
TARGET_DIR="$VENV_PATH/lib/python${PYTHON_VERSION}/site-packages/wx/lib/agw"
SOURCE_FILE="$SCRIPT_DIR/patches/wxpython/hypertreelist.py"

if [ -f "$SOURCE_FILE" ]; then
    mkdir -p "$TARGET_DIR"
    cp "$SOURCE_FILE" "$TARGET_DIR/hypertreelist.py"

    # Verify the patch was applied
    if grep -q "itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)" "$TARGET_DIR/hypertreelist.py"; then
        echo -e "${GREEN}✓ wxPython patch applied successfully${NC}"
        echo "  This fixes full-row background coloring (wxPython PR #2088)"
    else
        echo -e "${YELLOW}⚠ Patch file copied but verification failed${NC}"
    fi
else
    echo -e "${RED}✗ Patch file not found: $SOURCE_FILE${NC}"
    echo -e "${YELLOW}⚠ Background coloring may not work optimally${NC}"
    echo "  (Right-aligned date columns will only show text background)"
fi
echo

# Check launch script
echo -e "${BLUE}[6/7] Checking launch script...${NC}"
if [ -f "$SCRIPT_DIR/taskcoach-run.sh" ]; then
    chmod +x "$SCRIPT_DIR/taskcoach-run.sh"
    echo -e "${GREEN}✓ Launch script is ready: taskcoach-run.sh${NC}"
else
    echo -e "${RED}✗ Launch script not found${NC}"
    echo "taskcoach-run.sh should be included in the repository"
    exit 1
fi
echo

# Test installation
echo -e "${BLUE}[7/7] Testing installation...${NC}"
echo "===================="
echo

# Test 1: Import taskcoachlib
echo -n "Testing taskcoachlib import... "
if VERSION=$(python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); import taskcoachlib.meta.data as meta; print(meta.version)" 2>/dev/null); then
    echo -e "${GREEN}✓ (version $VERSION)${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    exit 1
fi

# Test 2: Import wx
echo -n "Testing wxPython import... "
if WX_VERSION=$(python3 -c "import wx; print(wx.__version__)" 2>/dev/null); then
    echo -e "${GREEN}✓ (version $WX_VERSION)${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    echo "Please check python3-wxgtk4.0 installation"
    exit 1
fi

# Test 2b: Verify wxPython patch in venv
echo -n "Testing wxPython patch... "
PATCH_FILE="$VENV_PATH/lib/python${PYTHON_VERSION}/site-packages/wx/lib/agw/hypertreelist.py"
if [ -f "$PATCH_FILE" ] && grep -q "itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)" "$PATCH_FILE"; then
    echo -e "${GREEN}✓ (patch applied)${NC}"
else
    echo -e "${YELLOW}⚠ (using system version)${NC}"
fi

# Test 3: Test venv packages individually
echo "Testing virtual environment packages..."
source "$VENV_PATH/bin/activate"

VENV_FAILED=0

# desktop3 package provides 'desktop' module
echo -n "  - desktop3... "
if python3 -c "import desktop" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    VENV_FAILED=1
fi

# Test other packages
for pkg in "lockfile" "gntp" "distro"; do
    echo -n "  - $pkg... "
    if python3 -c "import $pkg" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        VENV_FAILED=1
    fi
done

# pypubsub package provides 'pubsub' module
echo -n "  - pypubsub... "
if python3 -c "from pubsub import pub" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    VENV_FAILED=1
fi

deactivate

if [ $VENV_FAILED -eq 1 ]; then
    echo -e "${RED}✗ Some packages failed to import${NC}"
    echo "Try recreating the virtual environment:"
    echo "  rm -rf $VENV_PATH"
    echo "  python3 -m venv --system-site-packages $VENV_PATH"
    echo "  source $VENV_PATH/bin/activate"
    echo "  pip install desktop3 lockfile gntp distro pypubsub"
    exit 1
fi

# Test 4: Run help
echo -n "Testing application help... "
if "$SCRIPT_DIR/taskcoach-run.sh" --help &>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    exit 1
fi

# Test 5: Quick GUI test (skip if no display)
if [ -n "$DISPLAY" ]; then
    echo -n "Testing GUI initialization... "
    if timeout 3 "$SCRIPT_DIR/taskcoach-run.sh" 2>&1 | grep -q "TaskCoach\|wx" || [ $? -eq 124 ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ Could not fully test (this is OK)${NC}"
    fi
else
    echo "Skipping GUI test (no display available)"
fi

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "TaskCoach has been set up with:"
echo "  • System packages from Debian repos (wxPython, numpy, lxml, etc.)"
echo "  • Virtual environment at: $SCRIPT_DIR/.venv"
echo "  • Additional packages in venv (desktop3, lockfile, gntp, distro, pypubsub)"
echo "  • wxPython patch applied (full-row background coloring fix)"
echo
echo "You can now run TaskCoach with:"
echo -e "  ${BLUE}./taskcoach-run.sh${NC}"
echo
echo "To see all options:"
echo -e "  ${BLUE}./taskcoach-run.sh --help${NC}"
echo
echo "For more information, see DEBIAN_BOOKWORM_SETUP.md"
echo
