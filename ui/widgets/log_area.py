from __future__ import annotations

import tkinter as tk
from queue import Empty, Queue
from tkinter import scrolledtext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.log_service import LogService


class LogAreaWidget(tk.Frame):
    """Read-only scrollable log display subscribed to a :class:`LogService`.

    Entries are shown in ``[timestamp] message`` format and the widget
    auto-scrolls to the bottom on every new entry.  Because
    :class:`LogService` callbacks may arrive from a non-main thread, all
    widget mutations are scheduled on the main thread via a recurring
    ``after`` poll that drains a thread-safe queue.

    The callback :meth:`_on_new_log` only enqueues the entry and never
    touches any Tkinter object, so it is safe to invoke from any thread.
    """

    _DRAIN_INTERVAL_MS: int = 100

    def __init__(
        self,
        parent: tk.Widget,
        log_service: LogService,
        *,
        height: int = 10,
    ) -> None:
        super().__init__(parent)
        self._log_service = log_service
        self._callback = self._on_new_log

        # Thread-safe queue for entries arriving from any thread.
        self._queue: Queue[dict[str, str]] = Queue()

        # Title label
        self._title = tk.Label(self, text="日志", anchor="w")
        self._title.pack(fill=tk.X, pady=(0, 2))

        # Read-only scrolled text
        self._text = scrolledtext.ScrolledText(
            self,
            height=height,
            state="disabled",
            wrap=tk.WORD,
        )
        self._text.pack(fill=tk.BOTH, expand=True)

        self._log_service.subscribe(self._callback)
        self._start_polling()

    # ------------------------------------------------------------------
    # public methods
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all displayed log entries."""

        def _clear() -> None:
            self._text.configure(state="normal")
            self._text.delete("1.0", tk.END)
            self._text.configure(state="disabled")

        self.after(0, _clear)

    def destroy(self) -> None:
        """Unsubscribe from the log service and destroy the widget."""
        self._log_service.unsubscribe(self._callback)
        super().destroy()

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _on_new_log(self, entry: dict[str, str]) -> None:
        """Callback invoked by :class:`LogService` (potentially from any thread).

        This method is **thread-safe**: it only pushes to a
        :class:`queue.Queue` and never touches any Tkinter objects.
        The main-thread poller :meth:`_poll_loop` will pick up the
        entry on the next tick.
        """
        self._queue.put(entry)

    def _start_polling(self) -> None:
        """Begin the recurring main-thread poll loop."""
        self._poll_loop()

    def _poll_loop(self) -> None:
        """Drain the queue and reschedule (main thread only).

        Stops automatically once the widget is destroyed.
        """
        self._drain_pending()
        if self.winfo_exists():
            self.after(self._DRAIN_INTERVAL_MS, self._poll_loop)

    def _drain_pending(self) -> None:
        """Move every queued entry into the text widget."""
        while True:
            try:
                entry = self._queue.get_nowait()
            except Empty:
                break
            self._append_to_widget(entry)

    def _append_to_widget(self, entry: dict[str, str]) -> None:
        """Append a single formatted log entry to the text widget."""
        line = f"[{entry['timestamp']}] {entry['message']}\n"

        self._text.configure(state="normal")
        self._text.insert(tk.END, line)
        self._text.see(tk.END)
        self._text.configure(state="disabled")
