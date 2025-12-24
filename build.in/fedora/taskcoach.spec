# Task Coach - Your friendly task manager
# Fedora/RHEL/CentOS RPM Spec File
#
# Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>
# Copyright (C) 2008 Marcin Zajaczkowski <mszpak@wp.pl>
# Copyright (C) 2024 Aaron Wolf <https://github.com/realcarbonneau>
#
# Task Coach is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

Name:           taskcoach
Version:        1.6.1.73
Release:        1%{?dist}
Summary:        Your friendly task manager

License:        GPL-3.0-or-later
URL:            https://github.com/realcarbonneau/taskcoach
Source0:        %{url}/archive/refs/heads/main.tar.gz#/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

Requires:       python3 >= 3.8
Requires:       python3-wxpython4 >= 4.2.0
Requires:       python3-six >= 1.16.0
Requires:       python3-pypubsub
Requires:       python3-watchdog >= 3.0
Requires:       python3-chardet >= 5.2.0
Requires:       python3-dateutil >= 2.9.0
Requires:       python3-pyparsing >= 3.1.0
Requires:       python3-lxml
Requires:       python3-pyxdg
Requires:       python3-keyring
Requires:       python3-numpy
Requires:       python3-fasteners >= 0.19
Requires:       libXScrnSaver
Requires:       xdg-utils

# Optional dependencies
Recommends:     python3-zeroconf
Recommends:     espeak-ng

# squaremap and gntp not in Fedora repos - installed via pip at build time

%description
Task Coach is a simple open source todo manager to keep track of personal
tasks and todo lists. It is designed for composite tasks, and also offers
effort tracking, categories, notes and more.

Features:
- Composite tasks (subtasks)
- Effort tracking per task
- Categories and tags
- Notes attachments
- Reminders and recurring tasks
- Multiple views (tree, list, calendar, timeline)
- Import/Export capabilities
- Cross-platform (Linux, Windows, macOS)

%prep
%autosetup -n taskcoach-main

%build
%py3_build

%install
%py3_install

# Install wheel to ensure pip creates .dist-info (not .egg-info) on all distros
pip3 install wheel

# Install packages not available in Fedora repos
pip3 install --no-deps --target=%{buildroot}%{python3_sitelib} squaremap

# Install desktop file
install -Dm644 build.in/linux_common/taskcoach.desktop \
    %{buildroot}%{_datadir}/applications/%{name}.desktop

# Validate desktop file
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

# Install AppStream metadata
install -Dm644 build.in/debian/taskcoach.appdata.xml \
    %{buildroot}%{_metainfodir}/%{name}.appdata.xml

# Validate AppStream metadata
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/%{name}.appdata.xml

# Install icon
install -Dm644 icons.in/taskcoach.png \
    %{buildroot}%{_datadir}/pixmaps/%{name}.png

# Install Welcome.tsk for first-run experience
install -Dm644 Welcome.tsk \
    %{buildroot}%{_datadir}/%{name}/Welcome.tsk

%files
%license COPYRIGHT.txt
%doc README.md
%{_bindir}/taskcoach.py
%{python3_sitelib}/taskcoachlib/
%{python3_sitelib}/TaskCoach-*.egg-info/
%{python3_sitelib}/squaremap/
%{python3_sitelib}/squaremap-*.dist-info/
%{_datadir}/applications/%{name}.desktop
%{_metainfodir}/%{name}.appdata.xml
%{_datadir}/pixmaps/%{name}.png
%{_datadir}/%{name}/

%changelog
* Tue Dec 24 2024 Task Coach Developers <developers@taskcoach.org> - 1.6.1.73-1
- Modernized spec file for Fedora 39+/RHEL 9+/CentOS Stream 9+
- Added Python 3 support
- Added pip installation of squaremap (not in Fedora repos)
- Added AppStream metadata validation

* Mon Aug 15 2011 Jerome Laheurte <fraca7@free.fr> - 1.2.26-1
- Legacy: Apply patch from Oleg Tsarev for x64 systems
