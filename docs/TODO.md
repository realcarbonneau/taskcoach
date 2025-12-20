# Task Coach TODO

This document tracks planned improvements and known issues to address in future releases.

---

## Simultaneous Processes and Locking

### Current Status

| Resource | Locking | Status |
|----------|---------|--------|
| Task files (`.tsk`) | `fasteners.InterProcessLock` | ✅ Safe - uses `filename.tsk.lock` |
| INI file (`taskcoach.ini`) | `fasteners.InterProcessLock` | ✅ Safe - uses `taskcoach.ini.lock` |
| Log file (`taskcoachlog.txt`) | None | ⚠️ Shared between instances |

### TODO: Per-Process Log Files

Currently, all Task Coach instances write to the same `taskcoachlog.txt` file. While append mode is generally atomic, log entries from multiple instances can interleave, making debugging difficult.

**Proposed Solutions:**

1. **INI file setting** - Allow users to specify a custom log file path in settings:
   ```ini
   [file]
   logfile = /path/to/custom/taskcoachlog.txt
   ```

2. **Auto-numbered log files** - Automatically append instance number to log filename:
   - First instance: `taskcoachlog.txt`
   - Second instance: `taskcoachlog-2.txt`
   - Third instance: `taskcoachlog-3.txt`
   - etc.

**Implementation Notes:**
- Would need to detect if log file is already in use by another instance
- Could use `fasteners.InterProcessLock` on the log file to detect conflicts
- Instance number could be determined by trying locks sequentially

---

## Other TODOs

*Add future TODO items here as they are identified.*

---

**Last Updated:** December 2025
