from __future__ import annotations

import random
import threading
from typing import TYPE_CHECKING, Any

from models.action import Action
from models.enums import ActionType
from models.scheme import Scheme

if TYPE_CHECKING:
    from services.log_service import LogService


class MacroEngine:
    """Runs action sequences in a daemon thread.

    Executes a Scheme's actions sequentially on a background daemon thread.
    Supports looping (repeat until stopped) and single-pass execution.
    Uses threading.Event for graceful interruption.

    Dependencies are injected for testability:
        - log_service: object with an add(message: str) method
        - input_simulator: module with press_key, click_mouse, interruptible_sleep
    """

    def __init__(
        self,
        log_service: LogService,
        input_simulator: Any,
    ) -> None:
        """Initialise the macro engine.

        Args:
            log_service: Logger with add(message) method.
            input_simulator: Module providing press_key, click_mouse,
                and interruptible_sleep functions.
        """
        self._log = log_service
        self._sim = input_simulator
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        """True if a worker thread exists and is alive."""
        return self._thread is not None and self._thread.is_alive()

    def start(self, scheme: Scheme) -> bool:
        """Begin executing *scheme* on a daemon thread.

        Returns:
            True if execution started, False if already running.
        """
        if self.is_running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._execute, args=(scheme,), daemon=True
        )
        self._thread.start()
        self._log.add(f"启动方案：{scheme.name}")
        return True

    def stop(self) -> None:
        """Signal the worker thread to stop and wait up to 2 s for it."""
        self._stop_event.set()
        self._log.add("已停止")
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    # ── internal helpers ──────────────────────────────────────

    def _execute(self, scheme: Scheme) -> None:
        """Run *scheme* actions, looping if configured.  Entry-point for
        the daemon thread."""
        self._log.add(f"开始执行方案：{scheme.name}")
        try:
            while not self._stop_event.is_set():
                for action in scheme.actions:
                    if self._stop_event.is_set():
                        break
                    self._log.add(f"执行：{action}")
                    self._dispatch_action(action)
                if not scheme.loop:
                    break
        finally:
            self._log.add(f"方案执行结束：{scheme.name}")

    def _dispatch_action(self, action: Action) -> None:
        """Route *action* to the correct simulator function."""
        if action.action_type == ActionType.KEY_PRESS:
            self._sim.press_key(action.key, action.duration)
        elif action.action_type == ActionType.MOUSE_CLICK:
            self._sim.click_mouse(action.mouse_button, action.duration)
        elif action.action_type == ActionType.WAIT:
            if action.wait_seconds is not None:
                self._sim.interruptible_sleep(
                    action.wait_seconds, self._stop_event
                )
            else:
                assert action.wait_min is not None
                assert action.wait_max is not None
                seconds = random.uniform(action.wait_min, action.wait_max)
                self._sim.interruptible_sleep(seconds, self._stop_event)
