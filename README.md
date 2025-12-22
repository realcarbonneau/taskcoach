# Task Coach - Your friendly task manager

Task Coach is a simple open source todo manager to keep track of personal tasks and todo lists.

## Quick Start

Download and install the latest `.deb` package:

```bash
# Download the latest release
wget https://github.com/realcarbonneau/taskcoach/releases/latest/download/taskcoach_1.6.1_all.deb

# Install (handles all dependencies automatically)
sudo apt install ./taskcoach_1.6.1_all.deb

# Run
taskcoach
```

To uninstall: `sudo apt remove taskcoach`

## Running from Source

For development or if you prefer running from git:

```bash
git clone --depth 1 https://github.com/realcarbonneau/taskcoach.git
cd taskcoach
./setup.sh
./taskcoach-run.sh
```

See [docs/DEBIAN_BOOKWORM_SETUP.md](docs/DEBIAN_BOOKWORM_SETUP.md) for detailed setup options, troubleshooting, and platform-specific instructions.

## Testing

Run the test suite:

```bash
make unittests
```

For more options: `cd tests && python test.py --help`

## License

Task Coach is free software licensed under the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.html).

Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

## Architecture Overview

Task Coach is a desktop application developed in Python using wxPython for its GUI. It follows the Model-View-Controller pattern with three main layers:

- **Domain layer**: Classes for tasks, categories, effort, notes and other domain objects
- **GUI layer**: Viewers, controllers, dialogs, menus and other GUI components
- **Persistence layer**: Loading/saving domain objects to XML files (.tsk) and exporting to various formats

## Source Code Overview

Key packages:

| Package | Description |
|---------|-------------|
| `domain` | Domain objects (tasks, categories, effort, notes) |
| `gui` | Viewers, dialogs, and UI components |
| `command` | Undo/redo-capable user actions (Command pattern) |
| `config` | User settings and TaskCoach.ini handling |
| `persistence` | .tsk file format (XML) and export functionality |
| `i18n` | Internationalization and translations |
| `widgets` | Adapted wxPython widgets |

## Documentation

- [DEBIAN_BOOKWORM_SETUP.md](docs/DEBIAN_BOOKWORM_SETUP.md) - Detailed installation and setup
- [PACKAGING.md](docs/PACKAGING.md) - Building .deb packages
- [CRITICAL_WXPYTHON_PATCH.md](docs/CRITICAL_WXPYTHON_PATCH.md) - wxPython compatibility patch details

## Support

- GitHub Issues: https://github.com/realcarbonneau/taskcoach/issues
