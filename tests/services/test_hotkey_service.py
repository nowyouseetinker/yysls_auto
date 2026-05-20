from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from models.action import Action
from models.scheme import Scheme
from services.hotkey_service import HotkeyService

# ── fixtures ──────────────────────────────────────────────────


@pytest.fixture
def mock_kb() -> MagicMock:
    """Mock keyboard_hook module."""
    kb = MagicMock()
    kb.register_hotkey = MagicMock()
    kb.unregister_hotkey = MagicMock()
    kb.clear_all = MagicMock()
    return kb


@pytest.fixture
def mock_engine() -> MagicMock:
    """Mock MacroEngine."""
    engine = MagicMock()
    engine.start = MagicMock(return_value=True)
    engine.stop = MagicMock()
    engine.is_running = False
    return engine


@pytest.fixture
def mock_log() -> MagicMock:
    """Mock LogService."""
    return MagicMock()


@pytest.fixture
def sample_scheme() -> Scheme:
    """A minimal scheme for testing hotkey registration."""
    return Scheme.create(
        name="TestScheme",
        description="For testing",
        actions=(Action.key_press("1", order=0),),
        start_hotkey="F10",
        stop_hotkey="F12",
    )


@pytest.fixture
def custom_scheme() -> Scheme:
    """A scheme with non-default hotkeys."""
    return Scheme.create(
        name="Custom",
        description="Custom hotkeys",
        actions=(Action.key_press("2", order=0),),
        start_hotkey="ctrl+shift+a",
        stop_hotkey="ctrl+shift+b",
    )


@pytest.fixture
def service(
    mock_kb: MagicMock,
    mock_engine: MagicMock,
    mock_log: MagicMock,
) -> HotkeyService:
    return HotkeyService(
        keyboard_hook=mock_kb,
        macro_engine=mock_engine,
        log_service=mock_log,
    )


# ── 12.1  __init__ ────────────────────────────────────────────


class TestInit:
    def test_attributes_set(
        self,
        service: HotkeyService,
        mock_kb: MagicMock,
        mock_engine: MagicMock,
        mock_log: MagicMock,
    ) -> None:
        assert service._kb is mock_kb
        assert service._engine is mock_engine
        assert service._log is mock_log
        assert service._current_start_key is None
        assert service._current_stop_key is None
        assert service._current_scheme is None


# ── 12.2  _on_start / _on_stop ────────────────────────────────


class TestOnStart:
    def test_logs_and_starts_engine(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        mock_log: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        service._current_scheme = sample_scheme
        service._on_start()
        mock_log.add.assert_called_once_with("F10 启动")
        mock_engine.start.assert_called_once_with(sample_scheme)

    def test_noop_when_no_scheme(
        self,
        service: HotkeyService,
        mock_engine: MagicMock,
    ) -> None:
        service._on_start()
        mock_engine.start.assert_not_called()

    def test_uses_scheme_hotkey_not_hardcoded(
        self,
        service: HotkeyService,
        custom_scheme: Scheme,
        mock_log: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        service._current_scheme = custom_scheme
        service._on_start()
        mock_log.add.assert_called_once_with("ctrl+shift+a 启动")
        mock_engine.start.assert_called_once_with(custom_scheme)

    def test_already_running_is_noop(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        mock_engine: MagicMock,
        mock_log: MagicMock,
    ) -> None:
        """Pressing start when already running: engine.start returns False."""
        mock_engine.start.return_value = False
        service._current_scheme = sample_scheme
        service._on_start()
        # Still logs the key press
        mock_log.add.assert_called_once()
        # Still calls engine.start (engine itself handles the no-op)
        mock_engine.start.assert_called_once_with(sample_scheme)


class TestOnStop:
    def test_logs_and_stops_engine(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        mock_log: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        service._current_scheme = sample_scheme
        service._on_stop()
        mock_log.add.assert_called_once_with("F12 停止")
        mock_engine.stop.assert_called_once_with()

    def test_noop_when_no_scheme(
        self,
        service: HotkeyService,
        mock_engine: MagicMock,
    ) -> None:
        service._on_stop()
        mock_engine.stop.assert_not_called()

    def test_uses_scheme_hotkey_not_hardcoded(
        self,
        service: HotkeyService,
        custom_scheme: Scheme,
        mock_log: MagicMock,
        mock_engine: MagicMock,
    ) -> None:
        service._current_scheme = custom_scheme
        service._on_stop()
        mock_log.add.assert_called_once_with("ctrl+shift+b 停止")
        mock_engine.stop.assert_called_once_with()


# ── 12.3  register_hotkeys ────────────────────────────────────


class TestRegisterHotkeys:
    def test_registers_both_hotkeys(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        mock_kb: MagicMock,
        mock_log: MagicMock,
    ) -> None:
        service.register_hotkeys(sample_scheme)
        expected_calls = [
            call(sample_scheme.start_hotkey, service._on_start),
            call(sample_scheme.stop_hotkey, service._on_stop),
        ]
        mock_kb.register_hotkey.assert_has_calls(expected_calls)
        assert mock_kb.register_hotkey.call_count == 2

    def test_tracks_current_keys(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
    ) -> None:
        service.register_hotkeys(sample_scheme)
        assert service._current_start_key == "F10"
        assert service._current_stop_key == "F12"

    def test_stores_current_scheme(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
    ) -> None:
        service.register_hotkeys(sample_scheme)
        assert service._current_scheme is sample_scheme

    def test_logs_registration(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        mock_log: MagicMock,
    ) -> None:
        service.register_hotkeys(sample_scheme)
        mock_log.add.assert_called_with(
            "已注册热键：F10 启动 / F12 停止"
        )

    def test_custom_hotkeys_registration(
        self,
        service: HotkeyService,
        custom_scheme: Scheme,
        mock_kb: MagicMock,
    ) -> None:
        service.register_hotkeys(custom_scheme)
        expected_calls = [
            call("ctrl+shift+a", service._on_start),
            call("ctrl+shift+b", service._on_stop),
        ]
        mock_kb.register_hotkey.assert_has_calls(expected_calls)
        assert service._current_start_key == "ctrl+shift+a"
        assert service._current_stop_key == "ctrl+shift+b"

    def test_unregisters_previous_before_new(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        custom_scheme: Scheme,
        mock_kb: MagicMock,
    ) -> None:
        """Registering a new scheme automatically unregisters the old."""
        service.register_hotkeys(sample_scheme)
        service.register_hotkeys(custom_scheme)
        # Should have unregistered the old keys
        mock_kb.unregister_hotkey.assert_any_call("F10")
        mock_kb.unregister_hotkey.assert_any_call("F12")
        # Only the new scheme's keys remain tracked
        assert service._current_start_key == "ctrl+shift+a"
        assert service._current_stop_key == "ctrl+shift+b"


# ── 12.4  unregister_current / clear_all ──────────────────────


class TestUnregisterCurrent:
    def test_unregisters_both_keys(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        mock_kb: MagicMock,
    ) -> None:
        service.register_hotkeys(sample_scheme)
        service.unregister_current()
        mock_kb.unregister_hotkey.assert_any_call("F10")
        mock_kb.unregister_hotkey.assert_any_call("F12")
        assert mock_kb.unregister_hotkey.call_count == 2

    def test_clears_tracked_keys(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
    ) -> None:
        service.register_hotkeys(sample_scheme)
        service.unregister_current()
        assert service._current_start_key is None
        assert service._current_stop_key is None

    def test_noop_when_nothing_registered(
        self,
        service: HotkeyService,
        mock_kb: MagicMock,
    ) -> None:
        service.unregister_current()
        mock_kb.unregister_hotkey.assert_not_called()

    def test_noop_when_keys_already_none(
        self,
        service: HotkeyService,
        mock_kb: MagicMock,
    ) -> None:
        """Multiple calls to unregister_current are safe."""
        service.register_hotkeys(
            Scheme.create(
                name="T",
                description="",
                actions=(Action.key_press("x", order=0),),
            )
        )
        service.unregister_current()
        # Second call should be a no-op
        service.unregister_current()
        assert mock_kb.unregister_hotkey.call_count == 2  # only from the first call


class TestClearAll:
    def test_calls_unregister_and_clear_all(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        mock_kb: MagicMock,
    ) -> None:
        service.register_hotkeys(sample_scheme)
        service.clear_all()
        # Should have unregistered both keys
        mock_kb.unregister_hotkey.assert_any_call("F10")
        mock_kb.unregister_hotkey.assert_any_call("F12")
        # And cleared all
        mock_kb.clear_all.assert_called_once_with()

    def test_clear_all_when_nothing_registered(
        self,
        service: HotkeyService,
        mock_kb: MagicMock,
    ) -> None:
        service.clear_all()
        mock_kb.unregister_hotkey.assert_not_called()
        mock_kb.clear_all.assert_called_once_with()


# ── set_current_scheme ────────────────────────────────────────


class TestSetCurrentScheme:
    def test_updates_scheme(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        custom_scheme: Scheme,
    ) -> None:
        service.set_current_scheme(sample_scheme)
        assert service._current_scheme is sample_scheme
        service.set_current_scheme(custom_scheme)
        assert service._current_scheme is custom_scheme

    def test_does_not_reregister_hotkeys(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        custom_scheme: Scheme,
        mock_kb: MagicMock,
    ) -> None:
        service.register_hotkeys(sample_scheme)
        mock_kb.register_hotkey.reset_mock()
        service.set_current_scheme(custom_scheme)
        # set_current_scheme must NOT re-register hotkeys
        mock_kb.register_hotkey.assert_not_called()
        # The hotkeys should still be the old ones
        assert service._current_start_key == "F10"

    def test_affects_on_start_target(
        self,
        service: HotkeyService,
        sample_scheme: Scheme,
        custom_scheme: Scheme,
        mock_engine: MagicMock,
    ) -> None:
        """After set_current_scheme, _on_start uses the updated scheme."""
        service.register_hotkeys(sample_scheme)
        service.set_current_scheme(custom_scheme)
        service._on_start()
        mock_engine.start.assert_called_once_with(custom_scheme)
