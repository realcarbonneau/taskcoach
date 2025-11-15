#!/usr/bin/env python3
"""
Simple script to patch wxPython 4.2.1 for full-row background coloring.
This applies the fix from wxPython PR #2088 without requiring a full upgrade.
"""

import os
import sys
import shutil
from datetime import datetime

def main():
    print("=" * 60)
    print("Task Coach - wxPython Background Patch")
    print("=" * 60)
    print()

    # Find wxPython installation
    print("Locating wxPython installation...")
    try:
        import wx.lib.agw
        wx_path = wx.lib.agw.__path__[0]
    except ImportError:
        print("✗ ERROR: Could not import wxPython.")
        print("  Make sure wxPython is installed: pip3 install wxPython")
        sys.exit(1)

    hypertree_file = os.path.join(wx_path, "hypertreelist.py")
    backup_file = f"{hypertree_file}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"Found wxPython at: {wx_path}")
    print(f"Target file: {hypertree_file}")
    print()

    # Check if file exists
    if not os.path.isfile(hypertree_file):
        print(f"✗ ERROR: hypertreelist.py not found at {hypertree_file}")
        sys.exit(1)

    # Read the file
    with open(hypertree_file, 'r') as f:
        content = f.read()

    # Check if already patched
    if "itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)" in content and \
       "dc.DrawRectangle(itemrect)" in content:
        # Check if it's in the right context
        if """            elif drawItemBackground:
                itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)
                dc.SetBrush(wx.Brush(colBg, wx.SOLID))
                dc.DrawRectangle(itemrect)
                dc.SetTextForeground(colText)""" in content:
            print("✓ This file appears to already be patched!")
            response = input("Do you want to re-apply the patch anyway? (y/N) ")
            if response.lower() not in ['y', 'yes']:
                print("Exiting without changes.")
                sys.exit(0)

    # Create backup
    print("Creating backup...")
    shutil.copy2(hypertree_file, backup_file)
    print(f"Backup saved to: {backup_file}")
    print()

    # Apply patch
    print("Applying patch...")

    old_code = """            elif drawItemBackground:

                pass
                # We have to colour the item background for each column separately
                # So it is better to move this functionality in the subsequent for loop.

            else:
                dc.SetTextForeground(colText)"""

    new_code = """            elif drawItemBackground:
                itemrect = wx.Rect(0, item.GetY() + off_h, total_w-1, total_h - off_h)
                dc.SetBrush(wx.Brush(colBg, wx.SOLID))
                dc.DrawRectangle(itemrect)
                dc.SetTextForeground(colText)
            else:
                dc.SetTextForeground(colText)"""

    if old_code in content:
        new_content = content.replace(old_code, new_code)

        # Write the patched file
        try:
            with open(hypertree_file, 'w') as f:
                f.write(new_content)
            print("✓ Patch applied successfully!")
        except PermissionError:
            print("✗ ERROR: Permission denied writing to wxPython library.")
            print("  Please run this script with sudo:")
            print(f"  sudo python3 {sys.argv[0]}")
            sys.exit(1)
    else:
        print("✗ ERROR: Could not find the expected code pattern to patch.")
        print("  This may mean:")
        print("  - wxPython version is different than expected")
        print("  - The file has already been modified")
        print("  - The patch location has changed")
        print()
        print("  Please check the file manually:")
        print(f"    {hypertree_file}")
        sys.exit(1)

    # Verify the patch
    print()
    print("Verifying patch...")
    with open(hypertree_file, 'r') as f:
        patched_content = f.read()

    if new_code in patched_content:
        print("✓ Patch verified successfully!")
    else:
        print("✗ WARNING: Could not verify patch.")
        print("  Restoring backup...")
        shutil.copy2(backup_file, hypertree_file)
        print("  Original file restored.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("Patch Complete!")
    print("=" * 60)
    print()
    print("Backup saved to:")
    print(f"  {backup_file}")
    print()
    print("Next steps:")
    print("1. Run Task Coach: python3 taskcoach.py")
    print("2. Create a category with a background color")
    print("3. Verify that all columns show full-width backgrounds")
    print("4. Check that date columns have full cell coloring")
    print()
    print("To restore the original file:")
    print(f"  sudo cp {backup_file} {hypertree_file}")
    print()

if __name__ == "__main__":
    main()
