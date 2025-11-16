# TaskCoach Linux Builds - Complete Comparison

## Overview

TaskCoach is now built in **three variants** to maximize compatibility across all Linux distributions:

| Variant | Base System | GLIBC | Compatibility | Size | Best For |
|---------|-------------|-------|---------------|------|----------|
| **Ubuntu 22.04** ⭐ | Ubuntu 22.04 | 2.35 | 2020+ distros | ~60MB | **Most users** |
| **Ubuntu 24.04** | Ubuntu 24.04 | 2.38 | 2024+ distros | ~60MB | Latest systems |
| **AppImage** 🌐 | Ubuntu 20.04 | 2.31 | 2016+ distros | ~80-100MB | Maximum portability |

## Quick Decision Guide

### ⚡ Fast Decision

**Most users should download: Ubuntu 22.04 build** ⭐

This works on:
- Ubuntu 20.04, 22.04, 24.04
- Debian Bullseye, Bookworm
- Most distributions from 2020 onwards

### 🔍 Detailed Decision Tree

```
1. Check your GLIBC version:
   $ ldd --version

2. Choose based on version:
   ┌─ GLIBC 2.38+ → Ubuntu 24.04 build (smallest, fastest)
   ├─ GLIBC 2.31-2.37 → Ubuntu 22.04 build ⭐ (RECOMMENDED)
   └─ GLIBC < 2.31 → AppImage 🌐 (works everywhere)

3. Not sure? → AppImage (can't go wrong!)
```

## Detailed Build Information

### Build 1: Ubuntu 22.04 (RECOMMENDED) ⭐

**Artifact Name:** `taskcoach-{version}-linux-x86_64-glibc2.35-ubuntu22.04`

**Built On:** Ubuntu 22.04 LTS
**GLIBC Version:** 2.35
**Python Version:** Auto-detected (3.10, 3.11, or 3.12 depending on system)
**wxPython Version:** 4.0.7+
**Package Format:** Single executable (PyInstaller onefile)

**Compatible With:**
- ✅ **Ubuntu:** 20.04, 20.10, 21.04, 21.10, 22.04, 22.10, 23.04, 23.10, 24.04
- ✅ **Debian:** Bullseye (11), Bookworm (12), Trixie (13)
- ✅ **Linux Mint:** 20, 21
- ✅ **Pop!_OS:** 20.04+
- ✅ **Elementary OS:** 6.0+
- ✅ **Fedora:** 32+
- ✅ **openSUSE:** Leap 15.3+
- ✅ Most distributions released 2020 or later

**NOT Compatible With:**
- ❌ Ubuntu 18.04 (GLIBC 2.27)
- ❌ Debian Buster (GLIBC 2.28)
- ❌ CentOS 7 (GLIBC 2.17)
- ❌ Distributions older than 2020

**Pros:**
- Small download size (~60MB)
- Fast startup
- Native performance
- Works on vast majority of modern systems

**Cons:**
- Requires GLIBC 2.31 or newer
- Won't run on older distributions

**How to Use:**
```bash
# Download the file
wget https://github.com/.../taskcoach-...-ubuntu22.04

# Make executable
chmod +x taskcoach-*-ubuntu22.04

# Run
./taskcoach-*-ubuntu22.04
```

---

### Build 2: Ubuntu 24.04 (Latest Systems)

**Artifact Name:** `taskcoach-{version}-linux-x86_64-glibc2.38-ubuntu24.04`

**Built On:** Ubuntu 24.04 LTS
**GLIBC Version:** 2.38
**Python Version:** Auto-detected (usually 3.12)
**wxPython Version:** 4.2.1+
**Package Format:** Single executable (PyInstaller onefile)

**Compatible With:**
- ✅ **Ubuntu:** 24.04+
- ✅ **Debian:** Trixie (13)+
- ✅ **Fedora:** 40+
- ✅ Very recent distributions (2024+)

**NOT Compatible With:**
- ❌ Ubuntu 22.04 and older (GLIBC < 2.38)
- ❌ Debian Bookworm and older
- ❌ Most distributions released before 2024

**Pros:**
- Newest features
- Latest security updates
- Smallest possible size
- Fastest performance

**Cons:**
- Very limited compatibility
- Only works on very new systems
- Most users should use Ubuntu 22.04 build instead

**When to Use:**
- You're running Ubuntu 24.04 or newer
- You specifically need the latest GLIBC features
- You know your system has GLIBC 2.38+

**How to Use:**
```bash
# Same as Ubuntu 22.04 build
chmod +x taskcoach-*-ubuntu24.04
./taskcoach-*-ubuntu24.04
```

---

### Build 3: AppImage (MAXIMUM COMPATIBILITY) 🌐

**Artifact Name:** `taskcoach-{version}-x86_64.AppImage`

**Built On:** Ubuntu 20.04 LTS
**GLIBC Version:** 2.31 (but bundles all dependencies)
**Python Version:** Auto-detected (usually 3.8 or 3.9)
**wxPython Version:** 4.0.7+
**Package Format:** AppImage (self-contained)

**Compatible With:**
- ✅ **Ubuntu:** 16.04, 18.04, 20.04, 22.04, 24.04+
- ✅ **Debian:** 9 (Stretch), 10 (Buster), 11 (Bullseye), 12 (Bookworm), 13 (Trixie)
- ✅ **CentOS / RHEL:** 7, 8, 9
- ✅ **Fedora:** 25+
- ✅ **openSUSE:** Leap 42.2+
- ✅ **Arch Linux:** Current
- ✅ **Linux Mint:** 18+
- ✅ **Elementary OS:** All versions
- ✅ **Pop!_OS:** All versions
- ✅ **Manjaro:** All versions
- ✅ Virtually any Linux distribution from 2016 onwards

**NOT Compatible With:**
- ❌ Extremely old distributions (pre-2016)
- ❌ Systems without GLIBC 2.17+ (very rare)

**Pros:**
- **Works everywhere** - highest compatibility
- **No installation required** - just download and run
- **Self-contained** - all dependencies bundled
- **Portable** - can run from USB drive
- **No system conflicts** - isolated from system packages

**Cons:**
- Larger download size (~80-100MB)
- Slightly slower first startup (extracts to /tmp)
- May require FUSE (usually available)

**When to Use:**
- You have an older system (Ubuntu 18.04, CentOS 7, etc.)
- Other builds don't work on your system
- You want maximum portability
- You want to run from USB drive
- You're not sure which build to use

**How to Use:**
```bash
# Download
wget https://github.com/.../taskcoach-*.AppImage

# Make executable
chmod +x taskcoach-*.AppImage

# Run
./taskcoach-*.AppImage

# Optional: Extract and run (if FUSE not available)
./taskcoach-*.AppImage --appimage-extract
./squashfs-root/AppRun
```

**Troubleshooting:**
- If FUSE is not available: Use `--appimage-extract` to extract and run
- If permission denied: Run `chmod +x` on the file
- If "cannot execute binary file": You may be on a 32-bit system (not supported)

---

## Size Comparison

| Build | Compressed | Extracted | Dependencies |
|-------|-----------|-----------|--------------|
| Ubuntu 22.04 | ~60MB | N/A (single file) | System GLIBC, GTK3 |
| Ubuntu 24.04 | ~60MB | N/A (single file) | System GLIBC, GTK3 |
| AppImage | ~80-100MB | ~150MB in /tmp | All bundled |

## Performance Comparison

| Build | Startup Time | Memory Usage | Performance |
|-------|--------------|--------------|-------------|
| Ubuntu 22.04 | Fast | Low | Native |
| Ubuntu 24.04 | Fast | Low | Native |
| AppImage | Medium* | Medium | Native |

*First startup extracts to /tmp, subsequent startups are fast

## Distribution Recommendations

### For Package Maintainers

If you're packaging TaskCoach for a distribution:

- **Ubuntu/Debian PPAs**: Use Ubuntu 22.04 build
- **Snap Store**: Use Ubuntu 22.04 build
- **Flatpak**: Use Ubuntu 22.04 build
- **AUR (Arch)**: Use Ubuntu 22.04 build or build from source
- **RPM (Fedora/RHEL)**: Use Ubuntu 22.04 build

### For End Users

Download priority:
1. **First try:** Ubuntu 22.04 build ⭐
2. **If that fails:** AppImage 🌐
3. **If on Ubuntu 24.04:** Ubuntu 24.04 build (optional, 22.04 also works)

## Technical Details

### GLIBC Compatibility Matrix

| Distribution | Release Year | GLIBC | 22.04 Build | 24.04 Build | AppImage |
|--------------|--------------|-------|-------------|-------------|----------|
| Ubuntu 18.04 | 2018 | 2.27 | ❌ | ❌ | ✅ |
| Ubuntu 20.04 | 2020 | 2.31 | ✅ | ❌ | ✅ |
| Ubuntu 22.04 | 2022 | 2.35 | ✅ | ❌ | ✅ |
| Ubuntu 24.04 | 2024 | 2.38 | ✅ | ✅ | ✅ |
| Debian 10 | 2019 | 2.28 | ❌ | ❌ | ✅ |
| Debian 11 | 2021 | 2.31 | ✅ | ❌ | ✅ |
| Debian 12 | 2023 | 2.36 | ✅ | ❌ | ✅ |
| CentOS 7 | 2014 | 2.17 | ❌ | ❌ | ✅ |
| CentOS 8 | 2019 | 2.28 | ❌ | ❌ | ✅ |
| Fedora 38 | 2023 | 2.37 | ✅ | ❌ | ✅ |
| Fedora 40 | 2024 | 2.39 | ✅ | ✅ | ✅ |

### Why Three Builds?

**GLIBC Version Lock:**
- Python's `libpython3.X.so` is compiled against a specific GLIBC version
- Binaries built on newer systems won't run on older systems
- GLIBC uses symbol versioning - can't be bundled in PyInstaller

**Solution:**
- Build on **Ubuntu 24.04** (GLIBC 2.38) for newest systems
- Build on **Ubuntu 22.04** (GLIBC 2.35) for broad compatibility ⭐
- Build **AppImage** on Ubuntu 20.04 for maximum compatibility 🌐

This gives users the best option for their specific system!

## Verification

To verify which build works on your system:

```bash
# Check GLIBC version
ldd --version

# Check Ubuntu version
lsb_release -a

# Check distribution
cat /etc/os-release

# Test a build
chmod +x taskcoach-*
./taskcoach-* --version
```

Expected output:
```
Task Coach 1.5.1
```

## Download Links

All builds are available as GitHub Actions artifacts:
- Go to: https://github.com/realcarbonneau/taskcoach/actions
- Click on latest successful workflow run
- Scroll to "Artifacts" section
- Download your preferred build

## Support

- **Issue Tracker:** https://github.com/realcarbonneau/taskcoach/issues
- **Documentation:** See README.md and PYINSTALLER_BUILD.md
- **Build Problems:** See PORTABLE_BUILD_OPTIONS.md

---

**Last Updated:** 2025-11-16
**Workflow:** `.github/workflows/build-linux-all.yml`
**Recommended:** Ubuntu 22.04 build for most users ⭐
**Maximum Compatibility:** AppImage for older systems 🌐
