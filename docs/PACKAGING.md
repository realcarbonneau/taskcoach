# Debian/Ubuntu Packaging Guide for Task Coach

This document describes the Debian packaging setup for Task Coach and how it relates to official Debian/Ubuntu packaging.

## Important: Upstream vs Debian Packaging

This repository contains an **upstream** `debian/` directory for local builds only. This is **NOT** the official Debian package.

### The Two Types of debian/ Directories

| Type | Location | Purpose |
|------|----------|---------|
| **Upstream debian/** | This repo (`debian/`) | Local testing, convenience builds |
| **Official Debian packaging** | Separate `debian/*` branches | Debian archive submission |

Per [DEP-14](https://dep-team.pages.debian.net/deps/dep14/), official Debian packaging should use:
- `upstream/latest` - Contains release tarball contents (no `debian/`)
- `debian/master` - Derived from upstream, contains official `debian/` packaging

### Why the Separation?

1. **Different maintainers** - Upstream developers vs Debian packagers
2. **Different workflows** - git-buildpackage (gbp) vs direct development
3. **Patch management** - Debian uses quilt patches in `debian/patches/`
4. **Release tracking** - Debian tracks upstream releases via `debian/watch`

### This Repository's debian/

The `debian/` in this repository:
- Is for **local testing** and **convenience builds**
- Is **excluded from release tarballs** via `.gitattributes`
- Uses `UNRELEASED` distribution (not for archive upload)
- Does NOT include `debian/watch` (that's for Debian to track upstream)

## Directory Structure

```
debian/
├── changelog          # Version history (UNRELEASED)
├── control            # Package metadata
├── copyright          # DEP-5 license info
├── gbp.conf           # git-buildpackage configuration
├── patches/
│   └── series         # Empty (see wxPython note below)
├── README.source      # Explains this is for local builds
├── rules              # Build instructions
├── source/
│   └── format         # 3.0 (quilt)
└── taskcoach.install  # Installation notes
```

**Note:** The `.gitattributes` file excludes `debian/` from `git archive` and GitHub release tarballs.

## Building Locally

### Quick Binary Build

```bash
# Install build dependencies
sudo apt install build-essential debhelper dh-python \
    python3-all python3-setuptools python3-distro devscripts

# Build binary package (no orig tarball needed)
dpkg-buildpackage -us -uc -b

# Package will be in parent directory
ls ../*.deb
```

### With Lintian Checks

```bash
dpkg-buildpackage -us -uc -b
lintian --info --display-info ../*.changes
```

### Building Source Package

Source packages (for PPA uploads) require an orig tarball:

```bash
# Get version from changelog
VERSION=$(dpkg-parsechangelog -S Version | cut -d- -f1)

# Create orig tarball (excludes debian/ and .git/)
tar --exclude='debian' --exclude='.git' \
    -czf ../taskcoach_${VERSION}.orig.tar.gz .

# Build source package
dpkg-buildpackage -us -uc -S

# Files created in parent directory:
# - taskcoach_X.Y.Z.orig.tar.gz (upstream source)
# - taskcoach_X.Y.Z-N.debian.tar.xz (debian/ directory)
# - taskcoach_X.Y.Z-N.dsc (source description)
```

## wxPython Patch Strategy

Task Coach requires a patch to wxPython's `hypertreelist.py` for correct background coloring. Since packages cannot modify system `python3-wxgtk4.0`, we bundle the patch.

### The Problem

- wxPython < 4.2.4 has bugs in `TR_FULL_ROW_HIGHLIGHT` and `TR_FILL_WHOLE_COLUMN_BACKGROUND`
- Fix merged upstream in wxPython 4.2.4 (October 28, 2025)
- Current Debian/Ubuntu versions ship older wxPython

### The Solution

1. **Bundled patch** at `taskcoachlib/patches/hypertreelist.py`
2. **Import hook** in `taskcoachlib/workarounds/monkeypatches.py`
3. **Redirects** `wx.lib.agw.hypertreelist` to bundled version
4. System wxPython remains unmodified

This works for all installation methods (Debian, Ubuntu, Fedora, pip, etc.).

### When to Remove

Remove when Debian/Ubuntu ship wxPython >= 4.2.4:
1. Remove import hook from `monkeypatches.py`
2. Remove `taskcoachlib/patches/` directory

## Dependencies

### Runtime Dependencies

```
python3 (>= 3.8)
python3-wxgtk4.0 (>= 4.2.0)
python3-six
python3-pubsub
python3-watchdog
python3-chardet
python3-dateutil
python3-pyparsing
python3-lxml
python3-xdg
python3-keyring
python3-numpy
python3-fasteners
libxss1
xdg-utils
```

### Optional Dependencies

```
python3-zeroconf     # iPhone sync service discovery
python3-squaremap    # Hierarchical data visualization
python3-gntp         # Growl notifications (not in all distros)
```

### Build Dependencies

```
debhelper-compat (= 13)
dh-python
python3-all
python3-setuptools
python3-distro
```

## Ubuntu PPA Publishing

The same `debian/` packaging works for Ubuntu PPAs with minor changes.

### Version Naming

Ubuntu packages use a suffix to distinguish from Debian:

```
# Debian (hypothetical official)
taskcoach (1.6.1-1) unstable; urgency=medium

# Ubuntu PPA
taskcoach (1.6.1-1~ppa1) noble; urgency=medium
```

### Publishing to a PPA

1. **Create a Launchpad account** at https://launchpad.net

2. **Set up PPA**:
   ```bash
   # Create PPA via Launchpad web interface
   # https://launchpad.net/~YOUR_USERNAME/+activate-ppa
   ```

3. **Update changelog** for Ubuntu:
   ```bash
   # Change UNRELEASED to Ubuntu codename
   dch -D noble -v "1.6.1-1~ppa1" "PPA release for Ubuntu Noble"
   ```

4. **Create orig tarball** (required for quilt format):
   ```bash
   # Get version from changelog
   VERSION=$(dpkg-parsechangelog -S Version | cut -d- -f1)

   # Create tarball excluding debian/ directory
   tar --exclude='debian' --exclude='.git' \
       -czf ../taskcoach_${VERSION}.orig.tar.gz .
   ```

5. **Build source package**:
   ```bash
   dpkg-buildpackage -us -uc -S
   ```

6. **Sign and upload**:
   ```bash
   debsign ../*.changes
   dput ppa:YOUR_USERNAME/YOUR_PPA ../*_source.changes
   ```

### Supported Ubuntu Releases

| Codename | Version | wxPython | Status |
|----------|---------|----------|--------|
| Noble | 24.04 LTS | 4.2.1 | Patch required |
| Jammy | 22.04 LTS | 4.1.1 | Patch required |
| Oracular | 24.10 | 4.2.1 | Patch required |

## Official Debian Packaging (For Debian Maintainers)

If you're a Debian maintainer preparing an official package:

### 1. Set Up DEP-14 Branches

```bash
# Create upstream branch from release tarball
git checkout --orphan upstream/latest
# Import tarball contents (no debian/)

# Create debian branch
git checkout -b debian/master upstream/latest
# Add official debian/ directory
```

### 2. Configure gbp

Create `debian/gbp.conf`:
```ini
[DEFAULT]
debian-branch = debian/master
upstream-branch = upstream/latest
pristine-tar = True
```

### 3. Add debian/watch

```
version=4
opts=filenamemangle=s/.+\/v?(\d\S+)\.tar\.gz/taskcoach-$1\.tar\.gz/ \
  https://github.com/realcarbonneau/taskcoach/tags .*/v?(\d[\d.]+)\.tar\.gz
```

### 4. File ITP Bug

```bash
reportbug --severity=wishlist --package=wnpp \
  --subject="ITP: taskcoach -- Personal task manager"
```

### 5. Request Sponsorship

- [debian-mentors mailing list](https://lists.debian.org/debian-mentors/)
- [mentors.debian.net](https://mentors.debian.net/)

## GitHub Actions CI

### Automated .deb Builds

```yaml
name: Build Debian Package

on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build-deb:
    runs-on: ubuntu-latest
    container: debian:bookworm

    steps:
      - uses: actions/checkout@v4

      - name: Install build dependencies
        run: |
          apt-get update
          apt-get install -y build-essential debhelper dh-python \
            python3-all python3-setuptools python3-distro devscripts

      - name: Build package
        run: dpkg-buildpackage -us -uc -b

      - name: Run lintian
        run: |
          apt-get install -y lintian
          lintian --info ../*.changes || true

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: debian-package
          path: ../*.deb
```

### Multi-Distribution Matrix

```yaml
jobs:
  build:
    strategy:
      matrix:
        include:
          - distro: debian:bookworm
            name: bookworm
          - distro: debian:trixie
            name: trixie
          - distro: ubuntu:noble
            name: noble
    runs-on: ubuntu-latest
    container: ${{ matrix.distro }}
    # ... build steps
```

## References

### Debian Packaging
- [Debian New Maintainers' Guide](https://www.debian.org/doc/manuals/maint-guide/)
- [Debian Policy Manual](https://www.debian.org/doc/debian-policy/)
- [DEP-14: Git packaging layout](https://dep-team.pages.debian.net/deps/dep14/)
- [DEP-5: Machine-readable copyright](https://dep-team.pages.debian.net/deps/dep5/)
- [Python Policy](https://www.debian.org/doc/packaging-manuals/python-policy/)

### Git Workflows
- [PackagingWithGit - Debian Wiki](https://wiki.debian.org/PackagingWithGit)
- [git-buildpackage Manual](http://honk.sigxcpu.org/projects/git-buildpackage/manual-html/gbp.intro.html)

### Ubuntu
- [Launchpad PPA Documentation](https://help.launchpad.net/Packaging/PPA)
- [Ubuntu Packaging Guide](https://canonical-ubuntu-packaging-guide.readthedocs-hosted.com/)

### Desktop Integration
- [XDG Desktop Entry Spec](https://specifications.freedesktop.org/desktop-entry-spec/latest/)
- [AppStream Metadata](https://www.freedesktop.org/software/appstream/docs/)

## Related Documentation

- [CRITICAL_WXPYTHON_PATCH.md](CRITICAL_WXPYTHON_PATCH.md) - Detailed patch information
- [patches/wxpython/README.md](../patches/wxpython/README.md) - Patch installation methods
- [DEBIAN_BOOKWORM_SETUP.md](DEBIAN_BOOKWORM_SETUP.md) - Development setup on Bookworm
