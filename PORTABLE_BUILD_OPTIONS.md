# Portable Linux Build Options for TaskCoach

This document compares different approaches for creating portable Linux executables and explains how to bundle dependencies.

## The GLIBC Problem

The error you encountered:
```
Failed to load Python shared library: version `GLIBC_2.38' not found
```

This happens because PyInstaller executables **cannot bundle GLIBC** - they rely on the system's GLIBC. When you build on Ubuntu 24.04 (GLIBC 2.38), the executable won't run on systems with older GLIBC versions.

## Solution Comparison

| Solution | Portability | Size | Complexity | Best For |
|----------|-------------|------|------------|----------|
| **Build on old system** | Good | 60MB | Low | General use |
| **AppImage** | Excellent | 80-100MB | Medium | Maximum compatibility |
| **Flatpak** | Excellent | 60MB + runtime | High | Distribution via Flathub |
| **Static Python** | Good | 40-50MB | Very High | Advanced users |
| **Docker/Podman** | Perfect | 200MB+ | Medium | Server deployments |

## Option 1: Build on Ubuntu 22.04 (Current Solution) ✅

**Status:** Implemented in GitHub Actions workflow

**How it works:**
- Build on Ubuntu 22.04 (GLIBC 2.35)
- Executable works on any system with GLIBC 2.35+

**Compatibility:**
- ✅ Ubuntu 22.04+
- ✅ Ubuntu 20.04+ (GLIBC 2.31)
- ✅ Debian Bullseye+
- ✅ Debian Bookworm+
- ✅ Most distributions from 2020+
- ❌ Ubuntu 18.04 (GLIBC 2.27)

**Pros:**
- Simple - no extra tools needed
- Smallest executable size
- Fast build times
- Easy to maintain

**Cons:**
- Not compatible with very old systems
- Requires matching GLIBC version

## Option 2: AppImage (Maximum Portability) 🎯

**Status:** Build script provided (build-appimage.sh)

**How it works:**
- Packages the entire application with its dependencies
- Can include GLIBC if needed
- Single executable file
- No installation required

**Compatibility:**
- ✅ Ubuntu 16.04+
- ✅ Debian 9+
- ✅ CentOS 7+
- ✅ Any Linux from ~2016+

**Build steps:**
```bash
# 1. Install AppImage tools
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# 2. Build AppImage
./build-appimage.sh

# 3. Use the AppImage
chmod +x TaskCoach-x86_64.AppImage
./TaskCoach-x86_64.AppImage
```

**Pros:**
- Works on virtually any Linux distribution
- True portability - no system dependencies
- Can bundle old GLIBC for maximum compatibility
- Single file distribution
- Auto-update support available

**Cons:**
- Larger file size (~80-100MB)
- More complex build process
- Requires FUSE on some systems (or use --appimage-extract)

## Option 3: Flatpak (App Store Distribution)

**How it works:**
- Uses runtime environments (shared base systems)
- Sandboxed application
- Distributed via Flathub

**Compatibility:**
- ✅ Any distribution with Flatpak support
- ✅ Automatic updates via Flathub

**Build steps:**
```bash
# Create flatpak manifest
flatpak-builder --repo=repo build-dir org.taskcoach.TaskCoach.yml

# Install locally
flatpak build-bundle repo taskcoach.flatpak org.taskcoach.TaskCoach

# Or publish to Flathub
```

**Pros:**
- Official distribution channel
- Automatic updates
- Sandboxed security
- Shared runtimes reduce disk usage

**Cons:**
- Requires Flatpak runtime installation
- More complex packaging
- Requires Flatpak manifest maintenance
- Initial download includes runtime (~500MB first time)

## Option 4: Static Python Build (Advanced)

**How it works:**
- Build Python statically linked
- Bundle all C libraries
- Create truly standalone executable

**This is complex and generally NOT recommended because:**
1. wxPython has many dynamic dependencies (GTK3, X11, etc.)
2. Static linking GTK3 is extremely difficult
3. Some functionality requires dynamic loading (plugins, SSL certificates)
4. Build process is very complex

**Only consider if:**
- You're willing to spend significant time on build scripts
- You need the absolute smallest size
- You understand the trade-offs

## Option 5: Docker/Podman Container

**How it works:**
- Package entire application in a container
- Run with container runtime

**Compatibility:**
- ✅ Any system with Docker/Podman
- ✅ Works identically everywhere

**Usage:**
```bash
# Build container
docker build -t taskcoach .

# Run
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix taskcoach
```

**Pros:**
- Perfect reproducibility
- Complete isolation
- Easy distribution

**Cons:**
- Requires Docker/Podman installed
- Large size (200MB+)
- Complex X11 forwarding for GUI
- Overkill for desktop applications

## Recommendation by Use Case

### For General Desktop Users
**Use:** Option 1 (Build on Ubuntu 22.04) ✅
- Works on most modern systems
- Simplest distribution
- Smallest download

### For Maximum Compatibility
**Use:** Option 2 (AppImage) 🎯
- Works on systems back to 2016
- Single-file distribution
- No installation needed
- Best for "just works" experience

### For App Store Distribution
**Use:** Option 3 (Flatpak)
- Professional distribution channel
- Automatic updates
- Security sandboxing

### For Server/Headless Deployment
**Use:** Option 5 (Docker)
- Complete isolation
- Easy deployment

## Can PyInstaller Bundle GLIBC?

**Short answer: No, not practically.**

**Technical explanation:**

1. **Python's libpython is pre-compiled**: The `libpython3.12.so.1.0` file was compiled against a specific GLIBC version

2. **GLIBC symbol versioning**: GLIBC uses symbol versioning, so even if you bundle GLIBC, the Python library expects specific symbol versions

3. **System integration**: GLIBC integrates deeply with:
   - Kernel system calls
   - Name Service Switch (NSS) for DNS/users/groups
   - Thread-local storage (TLS)
   - Dynamic linker (/lib64/ld-linux-x86-64.so.2)

4. **Static linking issues**: Statically linking GLIBC:
   - Breaks DNS resolution (getaddrinfo, gethostbyname)
   - Breaks user/group lookups (getpwnam, getgrnam)
   - Breaks dynamic loading (dlopen)
   - Causes ABI incompatibilities

**What PyInstaller CAN bundle:**
- ✅ Python packages and modules
- ✅ wxPython libraries (wx.so files)
- ✅ GTK3 libraries (libgtk-3.so, etc.)
- ✅ Most application dependencies
- ❌ GLIBC (system library)
- ❌ Linux kernel headers
- ❌ System loader (ld-linux)

## Current GitHub Actions Implementation

The workflow now uses **Option 1** with these optimizations:

1. **Build on Ubuntu 22.04** (GLIBC 2.35)
2. **Auto-detect Python version** with wxPython support
3. **Validate GLIBC compatibility** in build info
4. **Test executable** before publishing

This provides the best balance of:
- Compatibility (works on systems from 2020+)
- Size (60MB)
- Simplicity (standard PyInstaller)
- Maintainability (simple CI/CD)

## Next Steps

If you need better compatibility than Ubuntu 22.04 provides, I recommend:

1. **Implement AppImage builds** using `build-appimage.sh`
2. **Update GitHub Actions** to build both PyInstaller and AppImage
3. **Distribute both versions**:
   - PyInstaller for modern systems (smaller, faster)
   - AppImage for maximum compatibility

Would you like me to implement AppImage builds in the GitHub Actions workflow?

---

**Last Updated:** 2025-11-16
**Recommended:** Option 1 (Ubuntu 22.04 PyInstaller) for general use
**Maximum Compatibility:** Option 2 (AppImage) if needed
