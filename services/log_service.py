from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime


class LogService:
    """Thread-safe logging service backed by a bounded deque with subscriber callbacks.

    Each log entry is a dict with ``timestamp`` (ISO 8601 UTC string) and ``message``
    keys.  Callbacks registered via :meth:`subscribe` are invoked synchronously on the
    calling thread whenever :meth:`add` is called, so subscribers are responsible for
    their own thread safety.
    """

    _MAX_ENTRIES: int = 500

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._logs: deque[dict[str, str]] = deque(maxlen=self._MAX_ENTRIES)
        self._subscribers: list[Callable[[dict[str, str]], None]] = []

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def add(self, message: str) -> None:
        """Append a timestamped log entry and notify every subscriber.

        Args:
            message: The log message text.  Must not be empty.
        """
        entry: dict[str, str] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": message,
        }

        with self._lock:
            self._logs.append(entry)
            # Take a snapshot of subscribers inside the lock so that the
            # iteration below is safe against concurrent subscribe /
            # unsubscribe calls.
            subscribers_snapshot = list(self._subscribers)

        for callback in subscribers_snapshot:
            callback(entry)

    def get_logs(self) -> list[dict[str, str]]:
        """Return a thread-safe snapshot of all buffered log entries.

        Returns:
            A list of dicts each containing ``timestamp`` and ``message``
            keys, ordered oldest-first.
        """
        with self._lock:
            return list(self._logs)

    def subscribe(self, callback: Callable[[dict[str, str]], None]) -> None:
        """Register *callback* to be called on every :meth:`add`.

        Duplicate registrations are silently ignored.

        Args:
            callback: A callable that accepts a single ``dict[str, str]`` argument.
        """
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[dict[str, str]], None]) -> None:
        """Remove a previously registered *callback*.

        Removing a callback that was never subscribed is a no-op.

        Args:
            callback: The callback to remove.
        """
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def clear(self) -> None:
        """Drop all buffered log entries (thread-safe)."""
        with self._lock:
            self._logs.clear()
