from __future__ import annotations

import customtkinter as ctk
from collections.abc import Callable
from typing import Any

from ui.theme import (
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    ACCENT_RED,
    ACCENT_RED_HOVER,
    BG_CARD,
    BORDER,
    BTN_DANGER,
    BTN_SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    label_font,
    small_font,
    FONT_FAMILY,
)


class StatusBarWidget(ctk.CTkFrame):
    """Modern status bar with semantic stop/start buttons and live info."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )

        self._on_start = on_start
        self._on_stop = on_stop
        self._running: bool = False

        # Grid: 5 columns, col 2 is spacer (weight=1 pushes buttons right)
        for i in range(5):
            self.columnconfigure(i, weight=0)
        self.columnconfigure(2, weight=1)

        # ── Left info labels ───────────────────────────────────
        self._scheme_label = ctk.CTkLabel(
            self, text="方案: --", font=label_font(), text_color=TEXT_PRIMARY, anchor="w",
        )
        self._scheme_label.grid(row=0, column=0, padx=(10, 4), pady=5, sticky="w")

        self._hotkey_label = ctk.CTkLabel(
            self, text="热键: -- / --", font=label_font(), text_color=TEXT_SECONDARY, anchor="w",
        )
        self._hotkey_label.grid(row=0, column=1, padx=4, pady=5, sticky="w")

        self._status_label = ctk.CTkLabel(
            self, text="○ 空闲", font=small_font(), text_color=TEXT_SECONDARY,
        )
        self._status_label.grid(row=0, column=3, padx=4, pady=5, sticky="w")

        self._elapsed_label = ctk.CTkLabel(
            self, text="--:--:--", font=small_font(), text_color=TEXT_SECONDARY,
        )
        self._elapsed_label.grid(row=0, column=4, padx=(2, 4), pady=5, sticky="w")

        # ── Right action buttons ───────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=5, padx=(4, 6), pady=4, sticky="e")

        self._start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ 启动",
            command=self._handle_start,
            **BTN_SUCCESS,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        )
        self._start_btn.pack(side=ctk.LEFT, padx=(0, 4))

        self._stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ 停止",
            command=self._handle_stop,
            state="disabled",
            **BTN_DANGER,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        )
        self._stop_btn.pack(side=ctk.LEFT)

    # ── Public API ─────────────────────────────────────────────

    def set_scheme(self, scheme: Any) -> None:
        self._scheme_label.configure(text=f"方案: {scheme.name}")
        self._hotkey_label.configure(
            text=f"热键: {scheme.start_hotkey} / {scheme.stop_hotkey}"
        )

    def set_running(self, running: bool) -> None:
        self._running = running
        self._refresh_status()
        self._refresh_buttons()

    def update_elapsed(self, seconds: float) -> None:
        self._elapsed_label.configure(text=self._format_elapsed(seconds))

    # ── Batch update (compat with main_window) ─────────────────

    def update_state(
        self,
        scheme_name: str | None = None,
        hotkeys: tuple[str, str] | None = None,
        is_running: bool | None = None,
        elapsed_seconds: float | None = None,
    ) -> None:
        if scheme_name is not None:
            self._scheme_label.configure(text=f"方案: {scheme_name}")
        if hotkeys is not None:
            self._hotkey_label.configure(
                text=f"热键: {hotkeys[0]} / {hotkeys[1]}"
            )
        if is_running is not None:
            self._running = is_running
            self._refresh_status()
            self._refresh_buttons()
        if elapsed_seconds is not None:
            self.update_elapsed(elapsed_seconds)

    # ── Internals ──────────────────────────────────────────────

    def _handle_start(self) -> None:
        if self._on_start is not None:
            self._on_start()

    def _handle_stop(self) -> None:
        if self._on_stop is not None:
            self._on_stop()

    def _refresh_status(self) -> None:
        if self._running:
            self._status_label.configure(
                text="● 运行中", text_color=ACCENT_GREEN
            )
        else:
            self._status_label.configure(
                text="○ 空闲", text_color=TEXT_SECONDARY
            )

    def _refresh_buttons(self) -> None:
        if self._running:
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="normal")
        else:
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        total = max(0, int(seconds))
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
