from __future__ import annotations

import threading
import time
import tkinter as tk

import pytest

from services.log_service import LogService
from ui.widgets.log_area import LogAreaWidget

# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------


def _flush_tk(root: tk.Tk) -> None:
    """Drive the Tk event loop so that pending ``after`` callbacks fire."""
    root.update_idletasks()
    root.update()
    # Let timed after callbacks become ready (poll interval is 100 ms).
    time.sleep(0.15)
    root.update_idletasks()
    root.update()


def _get_text(widget: LogAreaWidget) -> str:
    """Return the current text content of the log widget."""
    return widget._text.get("1.0", tk.END)


# ------------------------------------------------------------------
# fixtures
# ------------------------------------------------------------------


@pytest.fixture(scope="class")
def tk_root() -> tk.Tk:  # type: ignore[misc]
    """Provide a single Tk root per test class (avoids Windows resource exhaustion)."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def log_service() -> LogService:
    """Provide a fresh LogService instance."""
    return LogService()


@pytest.fixture
def widget(tk_root: tk.Tk, log_service: LogService) -> LogAreaWidget:
    """Provide a packed LogAreaWidget."""
    w = LogAreaWidget(tk_root, log_service)  # type: ignore[arg-type]
    w.pack()
    return w


# ------------------------------------------------------------------
# tests
# ------------------------------------------------------------------


class TestLogAreaWidgetCreation:
    def test_widget_creation(self, tk_root: tk.Tk, widget: LogAreaWidget) -> None:
        """A LogAreaWidget can be created and renders a title + empty text area."""
        _flush_tk(tk_root)
        assert widget._title.cget("text") == "日志"
        content = _get_text(widget)
        assert content.strip() == "" or content == "\n"

    def test_subscribes_on_creation(
        self, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """The widget subscribes to the LogService during __init__."""
        assert len(log_service._subscribers) == 1
        assert log_service._subscribers[0] is widget._callback


class TestLogCallback:
    def test_log_callback_appends_text(
        self, tk_root: tk.Tk, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """Adding a log entry via LogService causes the widget to display it."""
        log_service.add("Hello world")
        _flush_tk(tk_root)
        assert "Hello world" in _get_text(widget)

    def test_entries_have_timestamp_format(
        self, tk_root: tk.Tk, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """Each displayed entry follows the [timestamp] message format."""
        log_service.add("test message")
        _flush_tk(tk_root)
        content = _get_text(widget)
        assert content.startswith("[")
        assert "] test message" in content

    def test_multiple_entries_appear_in_order(
        self, tk_root: tk.Tk, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """Multiple log entries are appended oldest-first in the widget."""
        for i in range(5):
            log_service.add(f"msg {i}")
        _flush_tk(tk_root)

        content = _get_text(widget)
        lines = [ln for ln in content.strip().split("\n") if ln]
        assert len(lines) == 5
        for i, line in enumerate(lines):
            assert f"msg {i}" in line

    def test_entry_queued_before_flush(
        self, tk_root: tk.Tk, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """After add(), the entry is queued but NOT yet in the widget text."""
        log_service.add("before flush")
        assert "before flush" not in _get_text(widget)

        _flush_tk(tk_root)
        assert "before flush" in _get_text(widget)


class TestClear:
    def test_clear_removes_all_entries(
        self, tk_root: tk.Tk, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """clear() removes all displayed log text from the widget."""
        log_service.add("entry 1")
        log_service.add("entry 2")
        _flush_tk(tk_root)

        assert "entry 1" in _get_text(widget)
        assert "entry 2" in _get_text(widget)

        widget.clear()
        _flush_tk(tk_root)

        content = _get_text(widget)
        assert content.strip() == "" or content == "\n"

    def test_can_add_after_clear(
        self, tk_root: tk.Tk, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """After clearing, new entries continue to appear normally."""
        log_service.add("first")
        _flush_tk(tk_root)
        widget.clear()
        _flush_tk(tk_root)

        log_service.add("after clear")
        _flush_tk(tk_root)

        content = _get_text(widget)
        assert "after clear" in content
        assert "first" not in content


class TestDestroy:
    def test_destroy_unsubscribes(
        self, tk_root: tk.Tk, log_service: LogService
    ) -> None:
        """Destroying the widget unsubscribes from the LogService."""
        w = LogAreaWidget(tk_root, log_service)  # type: ignore[arg-type]
        w.pack()
        assert len(log_service._subscribers) == 1

        w.destroy()
        _flush_tk(tk_root)

        assert len(log_service._subscribers) == 0

    def test_destroy_then_add_does_not_crash(
        self, tk_root: tk.Tk, log_service: LogService
    ) -> None:
        """After destroy, log entries do not attempt to update the destroyed widget."""
        w = LogAreaWidget(tk_root, log_service)  # type: ignore[arg-type]
        w.pack()
        w.destroy()
        _flush_tk(tk_root)

        # This should not raise, even though the widget is gone
        log_service.add("after destroy")
        _flush_tk(tk_root)


class TestThreadSafety:
    def test_callback_from_non_main_thread_does_not_error(
        self, tk_root: tk.Tk, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """Simulate a LogService callback arriving from a background thread."""
        errors: list[Exception] = []

        def add_from_thread() -> None:
            try:
                log_service.add("from thread")
            except Exception as exc:
                errors.append(exc)

        t = threading.Thread(target=add_from_thread)
        t.start()
        t.join(timeout=2)

        _flush_tk(tk_root)

        assert len(errors) == 0
        assert "from thread" in _get_text(widget)

    def test_multiple_threads_enqueue_safely(
        self, tk_root: tk.Tk, log_service: LogService, widget: LogAreaWidget
    ) -> None:
        """Entries from multiple background threads all appear correctly."""
        errors: list[Exception] = []

        def add_msg(msg: str) -> None:
            try:
                log_service.add(msg)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=add_msg, args=(f"t{i}",)) for i in range(4)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2)

        _flush_tk(tk_root)

        assert len(errors) == 0
        content = _get_text(widget)
        for i in range(4):
            assert f"t{i}" in content
