"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from taskcoachlib import patterns
from pubsub import pub
from taskcoachlib.i18n import _
import wx
import logging
import threading

# Enable debug logging for AttributeSync
_log = logging.getLogger('AttributeSync')
_log.setLevel(logging.DEBUG)
# Add console handler if not already present
if not _log.handlers:
    _handler = logging.StreamHandler()
    _handler.setLevel(logging.DEBUG)
    _handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    _log.addHandler(_handler)


class AttributeSync(object):
    """Class used for keeping an attribute of a domain object synchronized with
    a control in a dialog. If the user edits the value using the control,
    the domain object is changed, using the appropriate command. If the
    attribute of the domain object is changed (e.g. in another dialog) the
    value of the control is updated.

    When debounce_ms > 0, command execution is delayed until typing stops.
    This creates a single undo entry for rapid edits (e.g., typing a date)."""

    def __init__(
        self,
        attributeGetterName,
        entry,
        currentValue,
        items,
        commandClass,
        editedEventType,
        changedEventType,
        callback=None,
        debounce_ms=0,
        **kwargs
    ):
        self._getter = attributeGetterName
        self._entry = entry
        self._currentValue = currentValue
        self._items = items
        self._commandClass = commandClass
        self.__commandKwArgs = kwargs
        self.__changedEventType = changedEventType
        self.__callback = callback
        self.__debounce_ms = debounce_ms
        self.__pendingValue = None
        self.__debounceTimer = None
        self.__timerLock = threading.Lock()  # Protect timer access across threads
        _log.debug("AttributeSync.__init__: getter=%s, entry=%s (%s), debounce_ms=%s, editedEventType=%s",
                   attributeGetterName, entry, type(entry).__name__, debounce_ms, editedEventType)
        # Note: debounce_ms > 0 means we use threading.Timer + wx.CallAfter
        # This avoids wx.Timer issues with widget hierarchies
        entry.Bind(editedEventType, self.onAttributeEdited)
        _log.debug("AttributeSync.__init__: Bound %s to onAttributeEdited", editedEventType)
        if len(items) == 1:
            self.__start_observing_attribute(changedEventType, items[0])

    def onAttributeEdited(self, event):
        _log.debug("onAttributeEdited: event=%s, event.GetEventType()=%s", event, event.GetEventType())
        event.Skip()
        new_value = self.getValue()
        _log.debug("onAttributeEdited: new_value=%s, current_value=%s, changed=%s",
                   new_value, self._currentValue, new_value != self._currentValue)
        if new_value != self._currentValue:
            if self.__debounce_ms > 0:
                # Debounced: store value and restart timer using threading.Timer + wx.CallAfter
                # This is more reliable than wx.Timer for composite widgets
                with self.__timerLock:
                    self.__pendingValue = new_value
                    # Cancel existing timer if any
                    if self.__debounceTimer is not None:
                        self.__debounceTimer.cancel()
                        _log.debug("onAttributeEdited: Cancelled existing timer")
                    # Start new timer (threading.Timer uses seconds, not ms)
                    delay_seconds = self.__debounce_ms / 1000.0
                    self.__debounceTimer = threading.Timer(delay_seconds, self.__onDebounceTimerThread)
                    self.__debounceTimer.daemon = True  # Don't block app exit
                    self.__debounceTimer.start()
                    _log.debug("onAttributeEdited: Started threading.Timer for %.3f seconds", delay_seconds)
            else:
                # Immediate: execute command now
                _log.debug("onAttributeEdited: executing command immediately (no debounce)")
                self.__executeCommand(new_value)

    def __onDebounceTimerThread(self):
        """Called on timer thread - use wx.CallAfter to execute on main thread."""
        _log.debug("__onDebounceTimerThread: Timer fired on thread %s, using wx.CallAfter",
                   threading.current_thread().name)
        # wx.CallAfter safely posts to the main thread's event queue
        wx.CallAfter(self.__onDebounceTimerMain)

    def __onDebounceTimerMain(self):
        """Called on main thread via wx.CallAfter - execute the command."""
        try:
            _log.debug("__onDebounceTimerMain: Executing on main thread, pendingValue=%s, entry=%s",
                       self.__pendingValue, self._entry)
            # Safety check: make sure the entry widget is still valid
            if self._entry and hasattr(self._entry, 'IsShown'):
                _log.debug("__onDebounceTimerMain: entry.IsShown()=%s", self._entry.IsShown())

            with self.__timerLock:
                pending = self.__pendingValue
                self.__pendingValue = None
                self.__debounceTimer = None

            if pending is not None:
                self.__executeCommand(pending)
            else:
                _log.debug("__onDebounceTimerMain: pendingValue is None, nothing to execute")
        except Exception as e:
            _log.exception("__onDebounceTimerMain: Exception occurred: %s", e)

    def __executeCommand(self, new_value):
        """Execute the command to update the model."""
        _log.debug("__executeCommand: executing command with new_value=%s", new_value)
        self._currentValue = new_value
        commandKwArgs = self.commandKwArgs(new_value)
        _log.debug("__executeCommand: commandClass=%s, items=%s, kwargs=%s",
                   self._commandClass, self._items, commandKwArgs)
        self._commandClass(
            None, self._items, **commandKwArgs
        ).do()  # pylint: disable=W0142
        _log.debug("__executeCommand: command executed successfully")
        self.__invokeCallback(new_value)

    def __cancelPendingDebounce(self):
        """Cancel any pending debounced change."""
        with self.__timerLock:
            self.__pendingValue = None
            if self.__debounceTimer is not None:
                self.__debounceTimer.cancel()
                self.__debounceTimer = None

    def onAttributeChanged_Deprecated(self, event):  # pylint: disable=W0613
        if self._entry:
            new_value = getattr(self._items[0], self._getter)()
            if new_value != self._currentValue:
                self._currentValue = new_value
                self.__cancelPendingDebounce()  # Cancel any pending debounced change
                self.setValue(new_value)
                self.__invokeCallback(new_value)
        else:
            self.__stop_observing_attribute()

    def onAttributeChanged(self, newValue, sender):
        if sender in self._items:
            if self._entry:
                if newValue != self._currentValue:
                    self._currentValue = newValue
                    self.__cancelPendingDebounce()  # Cancel any pending debounced change
                    self.setValue(newValue)
                    self.__invokeCallback(newValue)
            else:
                self.__stop_observing_attribute()

    def commandKwArgs(self, new_value):
        self.__commandKwArgs["newValue"] = new_value
        return self.__commandKwArgs

    def setValue(self, new_value):
        self._entry.SetValue(new_value)

    def getValue(self):
        return self._entry.GetValue()

    def __invokeCallback(self, value):
        if self.__callback is not None:
            try:
                self.__callback(value)
            except Exception as e:
                wx.MessageBox(str(e), _("Error"), wx.OK)

    def __start_observing_attribute(self, eventType, eventSource):
        if eventType.startswith("pubsub"):
            pub.subscribe(self.onAttributeChanged, eventType)
        else:
            patterns.Publisher().registerObserver(
                self.onAttributeChanged_Deprecated,
                eventType=eventType,
                eventSource=eventSource,
            )

    def __stop_observing_attribute(self):
        try:
            pub.unsubscribe(self.onAttributeChanged, self.__changedEventType)
        except pub.TopicNameError:
            pass
        patterns.Publisher().removeObserver(self.onAttributeChanged_Deprecated)


class FontColorSync(AttributeSync):
    def setValue(self, newValue):
        self._entry.SetColor(newValue)

    def getValue(self):
        return self._entry.GetColor()
