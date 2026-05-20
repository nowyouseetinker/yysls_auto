from __future__ import annotations

from typing import Any

from models.scheme import Scheme


class HotkeyService:
    """Coordinates between keyboard hooks and the macro engine.

    Registers global hotkeys (start / stop) for a given *Scheme*,
    routing hotkey callbacks to :class:`MacroEngine` and logging
    activity through :class:`LogService`.

    Dependencies are injected for testability:
        *keyboard_hook* -- module with ``register_hotkey``,
        ``unregister_hotkey``, and ``clear_all``.
        *macro_engine* -- has ``start(scheme) -> bool`` and
        ``stop()``.
        *log_service* -- has ``add(message: str)``.
    """

    def __init__(
        self,
        keyboard_hook: Any,
        macro_engine: Any,
        log_service: Any,
    ) -> None:
        """Initialise the hotkey service.

        Args:
            keyboard_hook: Module providing register_hotkey,
                unregister_hotkey, and clear_all functions.
            macro_engine: The :class:`MacroEngine` instance to
                orchestrate.
            log_service: The :class:`LogService` instance for
                recording hotkey events.
        """
        self._kb = keyboard_hook
        self._engine = macro_engine
        self._log = log_service
        self._current_start_key: str | None = None
        self._current_stop_key: str | None = None
        self._current_scheme: Scheme | None = None

    # ── public API ─────────────────────────────────────────

    def register_hotkeys(self, scheme: Scheme) -> None:
        """Register start/stop hotkeys from *scheme*.

        Any previously registered hotkeys are unregistered first.
        """
        self.unregister_current()
        self._current_scheme = scheme
        self._current_start_key = scheme.start_hotkey
        self._current_stop_key = scheme.stop_hotkey
        self._kb.register_hotkey(scheme.start_hotkey, self._on_start)
        self._kb.register_hotkey(scheme.stop_hotkey, self._on_stop)
        self._log.add(
            f"已注册热键：{scheme.start_hotkey} 启动 / {scheme.stop_hotkey} 停止"
        )

    def unregister_current(self) -> None:
        """Remove currently registered hotkeys (no-op when none)."""
        if self._current_start_key is not None:
            self._kb.unregister_hotkey(self._current_start_key)
            self._current_start_key = None
        if self._current_stop_key is not None:
            self._kb.unregister_hotkey(self._current_stop_key)
            self._current_stop_key = None

    def clear_all(self) -> None:
        """Unregister current hotkeys and clear all keyboard hooks."""
        self.unregister_current()
        self._kb.clear_all()

    def set_current_scheme(self, scheme: Scheme) -> None:
        """Update which scheme the start hotkey will execute.

        This does **not** re-register hotkeys; it only updates the
        target scheme that :meth:`_on_start` passes to the engine.
        """
        self._current_scheme = scheme

    # ── internal callbacks ─────────────────────────────────

    def _on_start(self) -> None:
        """Start-hotkey callback -- log and start the macro engine."""
        if self._current_scheme is None:
            return
        key = self._current_scheme.start_hotkey
        self._log.add(f"{key} 启动")
        self._engine.start(self._current_scheme)

    def _on_stop(self) -> None:
        """Stop-hotkey callback -- log and stop the macro engine."""
        if self._current_scheme is None:
            return
        key = self._current_scheme.stop_hotkey
        self._log.add(f"{key} 停止")
        self._engine.stop()
