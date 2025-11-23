# Twisted Framework Removal - Migration Guide

## Overview

As of November 2024, Task Coach has removed its dependency on the Twisted framework. This document explains the rationale, what changed, and how to work with the new implementation.

## Why Twisted Was Removed

### Historical Context (2004-2010 era)
- Python had no `async/await` (added in Python 3.5, 2015)
- wxPython's async support was limited
- Twisted was the only mature async framework for Python
- iPhone sync was a major feature (pre-iCloud era)

### Problems with Twisted Integration
1. **Complexity without benefit**: For a desktop GUI app, wx's event loop is sufficient
2. **Two event loops**: wxreactor bridges Twisted + wx, creating subtle bugs (like shutdown race conditions)
3. **Modern alternatives exist**: wx.CallLater(), asyncio, watchdog, socketserver
4. **Maintenance burden**: Twisted is a large dependency with its own learning curve

## Migration Summary

| Original (Twisted) | Replacement | Location |
|-------------------|-------------|----------|
| `wxreactor.install()` + `reactor.run()` | `wx.App.MainLoop()` | application.py |
| `reactor.callLater(seconds, fn)` | `wx.CallLater(milliseconds, fn)` | scheduler.py |
| `twisted.internet.inotify.INotify` | `watchdog` library | fs_inotify.py |
| `deferToThread()` + `@inlineCallbacks` | `concurrent.futures.ThreadPoolExecutor` | viewer/task.py |
| `twisted.internet.defer.Deferred` | Custom `AsyncResult` class | bonjour.py |
| `twisted.internet.protocol.Protocol` | `socketserver.BaseRequestHandler` | protocol.py |
| `twisted.internet.protocol.ServerFactory` | `socketserver.ThreadingTCPServer` | protocol.py |
| `reactor.listenTCP()` | `ThreadingTCPServer` in background thread | protocol.py |

## Detailed Changes

### 1. Application Event Loop (application.py)

**Before:**
```python
from twisted.internet import wxreactor
wxreactor.install()
# ... later ...
from twisted.internet import reactor
reactor.registerWxApp(self.__wx_app)
reactor.run()
```

**After:**
```python
# No special initialization needed
self.__wx_app.MainLoop()
```

**Note:** The wxreactor was a bridge that allowed Twisted's reactor to coexist with wxPython's event loop. This is no longer needed since we use wx's native event loop exclusively.

### 2. Task Scheduling (scheduler.py)

**Before:**
```python
from twisted.internet import reactor
self.__nextCall = reactor.callLater(nextDuration / 1000, self.__callback)
# Cancel with:
self.__nextCall.cancel()
```

**After:**
```python
import wx
self.__nextCall = wx.CallLater(nextDuration, self.__callback)
# Cancel with:
self.__nextCall.Stop()
```

**Important differences:**
- `reactor.callLater()` takes **seconds** (float)
- `wx.CallLater()` takes **milliseconds** (int)
- Cancel method: `.cancel()` → `.Stop()`

### 3. File System Monitoring (fs_inotify.py)

**Before:**
```python
from twisted.internet.inotify import INotify
from twisted.python.filepath import FilePath

self.notifier = INotify()
self.notifier.startReading()
self.notifier.watch(FilePath(path), callbacks=[self.onChange])
```

**After:**
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TaskFileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        wx.CallAfter(self.notifier.onFileChanged)

self._observer = Observer()
self._observer.schedule(handler, path, recursive=False)
self._observer.start()
```

**Benefits of watchdog:**
- Cross-platform (Linux inotify, macOS FSEvents, Windows ReadDirectoryChangesW)
- Pure Python, no Twisted reactor integration needed
- Active maintenance and community

### 4. Background Threading (viewer/task.py)

**Before:**
```python
from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks

@inlineCallbacks
def _refresh(self):
    yield deferToThread(igraph.plot, graph, filename, **style)
    # GUI update code here
```

**After:**
```python
from concurrent.futures import ThreadPoolExecutor

def _refresh(self):
    executor = ThreadPoolExecutor(max_workers=1)

    def do_plot():
        igraph.plot(graph, filename, **style)

    def on_complete(future):
        wx.CallAfter(update_gui)

    future = executor.submit(do_plot)
    future.add_done_callback(on_complete)
```

**Key pattern:** Always use `wx.CallAfter()` to update GUI from background threads.

### 5. Async Results (bonjour.py)

**Before:**
```python
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

d = Deferred()
d.callback(result)  # Success
d.errback(Failure(error))  # Error
return d
```

**After:**
```python
class AsyncResult:
    def __init__(self):
        self._callbacks = []
        self._errbacks = []

    def addCallback(self, cb): ...
    def addErrback(self, eb): ...
    def callback(self, result): ...
    def errback(self, error): ...

d = AsyncResult()
d.callback(result)  # Success
d.errback(error)  # Error (plain Exception, not Failure)
return d
```

### 6. Network Protocol (protocol.py)

**Before:**
```python
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor

class IPhoneHandler(Protocol):
    def connectionMade(self): ...
    def dataReceived(self, data): ...
    def connectionLost(self, reason): ...

class IPhoneAcceptor(ServerFactory):
    protocol = IPhoneHandler

    def __init__(self, ...):
        self.__listening = reactor.listenTCP(port, self)
```

**After:**
```python
import socketserver
import threading

class IPhoneHandler:
    def __init__(self, sock, ...):
        self.transport = SocketTransport(sock)

    def handle(self):
        self.connectionMade()
        while not closed:
            data = sock.recv(4096)
            self.dataReceived(data)
        self.connectionLost(None)

class IPhoneRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        handler = IPhoneHandler(self.request, ...)
        handler.handle()

class IPhoneAcceptor:
    def __init__(self, ...):
        self._server = socketserver.ThreadingTCPServer(('', port), IPhoneRequestHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
```

## Testing Changes

Tests that used `reactor.iterate()` to pump the event loop now use wx event processing:

**Before:**
```python
from twisted.internet import reactor
while time.time() - t0 < 2.0:
    reactor.iterate()
```

**After:**
```python
while time.time() - t0 < 2.0:
    wx.GetApp().Yield(True)
    time.sleep(0.05)  # Prevent CPU spin
```

The `@test.skipOnTwistedVersions()` decorator is now a no-op but kept for backward compatibility.

## Dependencies

### Removed
- `twisted` - The Twisted framework

### Added
- `watchdog>=3.0.0` - Cross-platform file system monitoring

### Already Present (unchanged)
- `zeroconf>=0.50.0` - For Bonjour/mDNS service discovery (iPhone sync)

## Potential Issues and Solutions

### Issue: wx.CallLater not firing
**Cause:** `wx.CallLater` requires the wx event loop to be running.
**Solution:** Ensure `MainLoop()` is running, or use `wx.GetApp().Yield()` in tests.

### Issue: GUI updates from background threads
**Cause:** wxPython is not thread-safe for GUI operations.
**Solution:** Always wrap GUI updates in `wx.CallAfter()`.

### Issue: Socket server not accepting connections
**Cause:** Server thread may not be started or port may be in use.
**Solution:** Check that `serve_forever()` is running in a daemon thread.

## Code Locations with Design Notes

All modified files contain `DESIGN NOTE (Twisted Removal - 2024):` comments explaining:
- What the original Twisted code did
- Why the replacement was chosen
- Any compatibility considerations

Search for these notes to find detailed explanations:
```bash
grep -r "DESIGN NOTE (Twisted Removal" taskcoachlib/
```

## References

- [wxPython CallLater documentation](https://docs.wxpython.org/wx.CallLater.html)
- [watchdog documentation](https://python-watchdog.readthedocs.io/)
- [Python socketserver documentation](https://docs.python.org/3/library/socketserver.html)
- [concurrent.futures documentation](https://docs.python.org/3/library/concurrent.futures.html)
