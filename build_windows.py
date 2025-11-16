#!/usr/bin/env python3
"""
Build script for creating Windows executable using PyInstaller.

This script can be run locally on Windows or is used by GitHub Actions.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")

    required_modules = [
        'PyInstaller',
        'wx',
        'twisted',
        'pubsub',
        'chardet',
        'dateutil',
        'pyparsing',
        'lxml',
        'keyring',
        'numpy',
        'lockfile',
        'gntp',
    ]

    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module} - MISSING")
            missing.append(module)

    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Please install missing dependencies first.")
        return False

    print("All dependencies found!")
    return True


def clean_build_directories():
    """Clean previous build artifacts."""
    print("\nCleaning previous build artifacts...")

    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"  Removing {dir_name}/")
            shutil.rmtree(dir_name)

    print("Clean complete!")


def build_executable():
    """Build the executable using PyInstaller."""
    print("\nBuilding Windows executable...")

    # Check if spec file exists
    spec_file = 'TaskCoach.spec'
    if not os.path.exists(spec_file):
        print(f"ERROR: {spec_file} not found!")
        return False

    # Run PyInstaller
    try:
        cmd = ['pyinstaller', spec_file, '--clean']
        print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        print(result.stdout)
        print("\nBuild completed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code {e.returncode}")
        print(e.output)
        return False


def verify_build():
    """Verify the build output."""
    print("\nVerifying build output...")

    exe_path = Path('dist/TaskCoach/TaskCoach.exe')

    if not exe_path.exists():
        print(f"ERROR: Executable not found at {exe_path}")
        return False

    file_size = exe_path.stat().st_size
    print(f"  ✓ Executable found: {exe_path}")
    print(f"  ✓ File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")

    # List contents of dist directory
    print("\nBuild output contents:")
    dist_path = Path('dist/TaskCoach')
    for item in sorted(dist_path.rglob('*')):
        if item.is_file():
            size = item.stat().st_size
            rel_path = item.relative_to(dist_path)
            print(f"  {rel_path} ({size:,} bytes)")

    return True


def create_zip():
    """Create a ZIP archive of the distribution."""
    print("\nCreating distribution archive...")

    try:
        zip_name = 'TaskCoach-Windows'
        shutil.make_archive(zip_name, 'zip', 'dist/TaskCoach')

        zip_path = Path(f'{zip_name}.zip')
        if zip_path.exists():
            size = zip_path.stat().st_size
            print(f"  ✓ Created: {zip_path}")
            print(f"  ✓ Archive size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
            return True
    except Exception as e:
        print(f"  ✗ Failed to create archive: {e}")
        return False


def main():
    """Main build process."""
    print("=" * 60)
    print("Task Coach - Windows Executable Build Script")
    print("=" * 60)

    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Build aborted due to missing dependencies.")
        sys.exit(1)

    # Step 2: Clean previous builds
    clean_build_directories()

    # Step 3: Build executable
    if not build_executable():
        print("\n❌ Build failed!")
        sys.exit(1)

    # Step 4: Verify build
    if not verify_build():
        print("\n❌ Build verification failed!")
        sys.exit(1)

    # Step 5: Create ZIP archive
    create_zip()

    print("\n" + "=" * 60)
    print("✅ Build completed successfully!")
    print("=" * 60)
    print("\nThe executable can be found in:")
    print("  dist/TaskCoach/TaskCoach.exe")
    print("\nZIP archive:")
    print("  TaskCoach-Windows.zip")
    print("\nYou can now test the executable or distribute the ZIP file.")


if __name__ == '__main__':
    main()
