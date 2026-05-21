from __future__ import annotations

import customtkinter as ctk
from queue import Empty, Queue
from typing import TYPE_CHECKING

from ui.theme import (
    BORDER,
    FONT_FAMILY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    label_font,
)

if TYPE_CHECKING:
    from services.log_service import LogService


class LogAreaWidget(ctk.CTkFrame):
    """Log display — Microsoft YaHei 10pt, timestamp coloring, auto-scroll."""

    _DRAIN_INTERVAL_MS: int = 100

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        log_service: LogService,
        *,
        height: int = 10,
    ) -> None:
        super().__init__(
            parent,
            fg_color="#FFFFFF",
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
        )

        self._log_service = log_service
        self._callback = self._on_new_log
        self._queue: Queue[dict[str, str]] = Queue()

        self._title = ctk.CTkLabel(
            self, text="日志", font=label_font(),
            text_color=TEXT_PRIMARY, anchor="w",
        )
        self._title.pack(fill=ctk.X, padx=10, pady=(6, 3))

        # Explicit Microsoft YaHei 10pt
        body_font = ctk.CTkFont(family=FONT_FAMILY, size=13)
        self._text = ctk.CTkTextbox(
            self,
            corner_radius=6,
            fg_color="#FAFBFC",
            border_width=1,
            border_color=BORDER,
            font=body_font,
            wrap="word",
            height=height,
            activate_scrollbars=True,
        )
        self._text.pack(fill=ctk.BOTH, expand=True, padx=8, pady=(0, 5))

        # Color-only tags
        self._text.tag_config("timestamp", foreground=TEXT_SECONDARY)
        self._text.tag_config("message", foreground=TEXT_PRIMARY)

        self._text.configure(state="disabled")

        self._log_service.subscribe(self._callback)
        self._start_polling()

    def clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    def destroy(self) -> None:
        self._log_service.unsubscribe(self._callback)
        super().destroy()

    def _on_new_log(self, entry: dict[str, str]) -> None:
        self._queue.put(entry)

    def _start_polling(self) -> None:
        self._poll_loop()

    def _poll_loop(self) -> None:
        self._drain_pending()
        if self.winfo_exists():
            self.after(self._DRAIN_INTERVAL_MS, self._poll_loop)

    def _drain_pending(self) -> None:
        while True:
            try:
                entry = self._queue.get_nowait()
            except Empty:
                break
            self._append_entry(entry)

    def _append_entry(self, entry: dict[str, str]) -> None:
        self._text.configure(state="normal")
        ts = f"[{entry['timestamp']}]  "
        msg = f"{entry['message']}\n"
        self._text.insert("end", ts, "timestamp")
        self._text.insert("end", msg, "message")
        self._text.see("end")
        self._text.configure(state="disabled")
