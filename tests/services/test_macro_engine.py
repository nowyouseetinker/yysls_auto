from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, Mock

import pytest

from models.action import Action
from models.enums import MouseButton
from models.scheme import Scheme
from services.macro_engine import MacroEngine

# ── fixtures ──────────────────────────────────────────────────


@pytest.fixture
def mock_log() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_sim() -> Mock:
    """Simulates the infra.input_simulator module."""
    sim = Mock()
    sim.press_key = Mock()
    sim.click_mouse = Mock()
    sim.interruptible_sleep = Mock()
    return sim


@pytest.fixture
def engine(mock_log: MagicMock, mock_sim: Mock) -> MacroEngine:
    return MacroEngine(log_service=mock_log, input_simulator=mock_sim)


@pytest.fixture
def single_shot_scheme() -> Scheme:
    """A non-looping scheme with two actions."""
    return Scheme.create(
        name="Single",
        description="One-shot",
        actions=(
            Action.key_press("1", order=0, duration=0.05),
            Action.wait_fixed(0.5, order=1),
        ),
        loop=False,
    )


@pytest.fixture
def loop_scheme() -> Scheme:
    """A looping scheme with a key-press then a tiny wait."""
    return Scheme.create(
        name="Loop",
        description="Repeats",
        actions=(
            Action.key_press("F", order=0, duration=0.01),
            Action.wait_fixed(0.01, order=1),
        ),
        loop=True,
    )


# ── 10.1  init + is_running ───────────────────────────────────


class TestInit:
    def test_not_running_initially(self, engine: MacroEngine) -> None:
        assert engine.is_running is False

    def test_thread_is_none_initially(self, engine: MacroEngine) -> None:
        assert engine._thread is None

    def test_stop_event_clear_initially(self, engine: MacroEngine) -> None:
        assert engine._stop_event.is_set() is False


# ── 10.2  start ────────────────────────────────────────────────


class TestStart:
    def test_creates_thread(self, engine: MacroEngine, single_shot_scheme: Scheme) -> None:
        result = engine.start(single_shot_scheme)
        assert result is True
        assert engine._thread is not None
        assert isinstance(engine._thread, threading.Thread)

    def test_thread_is_daemon(self, engine: MacroEngine, single_shot_scheme: Scheme) -> None:
        engine.start(single_shot_scheme)
        assert engine._thread.daemon is True  # type: ignore[union-attr]

    def test_is_running_after_start(self, engine: MacroEngine, loop_scheme: Scheme) -> None:
        """Use a looping scheme so the thread stays alive for the assertion."""
        engine.start(loop_scheme)
        assert engine.is_running is True
        engine.stop()

    def test_returns_false_when_already_running(
        self, engine: MacroEngine, loop_scheme: Scheme
    ) -> None:
        engine.start(loop_scheme)
        result = engine.start(loop_scheme)
        assert result is False
        engine.stop()

    def test_logs_start_event(
        self,
        engine: MacroEngine,
        single_shot_scheme: Scheme,
        mock_log: MagicMock,
    ) -> None:
        engine.start(single_shot_scheme)
        engine._thread.join(timeout=2.0)  # type: ignore[union-attr]
        start_calls = [
            c[0][0] for c in mock_log.add.call_args_list
            if "启动方案" in c[0][0]
        ]
        assert len(start_calls) >= 1


# ── 10.3  _execute ─────────────────────────────────────────────


class TestExecute:
    def test_single_pass_dispatches_actions(
        self, engine: MacroEngine, single_shot_scheme: Scheme, mock_sim: Mock
    ) -> None:
        engine.start(single_shot_scheme)
        engine._thread.join(timeout=2.0)  # type: ignore[union-attr]
        assert not engine.is_running
        mock_sim.press_key.assert_called_once_with("1", 0.05)
        mock_sim.interruptible_sleep.assert_called_once_with(
            0.5, engine._stop_event
        )

    def test_loop_repeats_actions(
        self, engine: MacroEngine, loop_scheme: Scheme, mock_sim: Mock
    ) -> None:
        engine.start(loop_scheme)
        # Let a few iterations run (sleep is mocked, so very fast)
        time.sleep(0.05)
        engine.stop()
        # Should have been called at least twice
        assert mock_sim.press_key.call_count >= 2

    def test_logs_action_execution(
        self, engine: MacroEngine, single_shot_scheme: Scheme, mock_log: MagicMock
    ) -> None:
        engine.start(single_shot_scheme)
        engine._thread.join(timeout=2.0)  # type: ignore[union-attr]
        execute_calls = [
            c[0][0] for c in mock_log.add.call_args_list
            if "执行：" in c[0][0]
        ]
        assert len(execute_calls) == 2  # one per action

    def test_logs_begin_and_end(
        self, engine: MacroEngine, single_shot_scheme: Scheme, mock_log: MagicMock
    ) -> None:
        engine.start(single_shot_scheme)
        engine._thread.join(timeout=2.0)  # type: ignore[union-attr]
        messages = [c[0][0] for c in mock_log.add.call_args_list]
        assert any("开始执行" in m for m in messages)
        assert any("执行结束" in m for m in messages)

    def test_checks_stop_event_before_each_action(
        self, engine: MacroEngine, loop_scheme: Scheme, mock_sim: Mock
    ) -> None:
        """When the first action sets stop_event, subsequent actions are skipped."""
        call_count = 0

        def set_stop_on_first(*args: object, **kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            engine._stop_event.set()

        mock_sim.press_key.side_effect = set_stop_on_first
        engine.start(loop_scheme)
        engine._thread.join(timeout=2.0)  # type: ignore[union-attr]
        # Only the action that set stop_event should have been dispatched
        assert call_count == 1

    def test_single_pass_stops_mid_sequence_on_event(
        self, engine: MacroEngine, mock_sim: Mock
    ) -> None:
        """When stop_event is set mid-sequence in non-loop mode, exit cleanly."""
        # Build a scheme with 3 actions
        scheme = Scheme.create(
            name="MidStop",
            description="",
            actions=(
                Action.key_press("a", order=0),
                Action.key_press("b", order=1),
                Action.key_press("c", order=2),
            ),
            loop=False,
        )
        # Make the first press_key call set the stop event
        def set_stop(*args: object, **kwargs: object) -> None:
            engine._stop_event.set()

        mock_sim.press_key.side_effect = set_stop
        engine.start(scheme)
        engine._thread.join(timeout=2.0)  # type: ignore[union-attr]
        # Only the first action should have been dispatched
        assert mock_sim.press_key.call_count == 1


# ── 10.4  _dispatch_action ─────────────────────────────────────


class TestDispatchAction:
    def test_key_press(self, engine: MacroEngine, mock_sim: Mock) -> None:
        action = Action.key_press("Space", order=0, duration=0.3)
        engine._dispatch_action(action)
        mock_sim.press_key.assert_called_once_with("Space", 0.3)
        mock_sim.click_mouse.assert_not_called()

    def test_mouse_click_left(self, engine: MacroEngine, mock_sim: Mock) -> None:
        action = Action.mouse_click(MouseButton.LEFT, order=0, duration=0.15)
        engine._dispatch_action(action)
        mock_sim.click_mouse.assert_called_once_with(MouseButton.LEFT, 0.15)

    def test_mouse_click_right(self, engine: MacroEngine, mock_sim: Mock) -> None:
        action = Action.mouse_click(MouseButton.RIGHT, order=1, duration=0.2)
        engine._dispatch_action(action)
        mock_sim.click_mouse.assert_called_once_with(MouseButton.RIGHT, 0.2)

    def test_wait_fixed(self, engine: MacroEngine, mock_sim: Mock) -> None:
        action = Action.wait_fixed(2.5, order=0)
        engine._dispatch_action(action)
        mock_sim.interruptible_sleep.assert_called_once_with(
            2.5, engine._stop_event
        )

    def test_wait_random_calls_sleep_with_value_in_range(
        self, engine: MacroEngine, mock_sim: Mock
    ) -> None:
        action = Action.wait_random(1.0, 5.0, order=0)
        engine._dispatch_action(action)
        call_args = mock_sim.interruptible_sleep.call_args
        seconds = call_args[0][0]
        assert 1.0 <= seconds <= 5.0
        assert call_args[0][1] is engine._stop_event

    def test_wait_random_uses_uniform_distribution(
        self, engine: MacroEngine, mock_sim: Mock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify random.uniform is called with (wait_min, wait_max)."""
        called_with: list[tuple[float, float]] = []

        def fake_uniform(a: float, b: float) -> float:
            called_with.append((a, b))
            return 3.0

        monkeypatch.setattr("services.macro_engine.random.uniform", fake_uniform)
        action = Action.wait_random(2.0, 8.0, order=0)
        engine._dispatch_action(action)
        assert called_with == [(2.0, 8.0)]
        mock_sim.interruptible_sleep.assert_called_once_with(3.0, engine._stop_event)


# ── 10.5  stop ─────────────────────────────────────────────────


class TestStop:
    def test_sets_stop_event(self, engine: MacroEngine) -> None:
        engine.stop()
        assert engine._stop_event.is_set()

    def test_is_running_false_after_stop(
        self, engine: MacroEngine, loop_scheme: Scheme
    ) -> None:
        engine.start(loop_scheme)
        assert engine.is_running is True
        engine.stop()
        assert engine.is_running is False

    def test_logs_stop_event(self, engine: MacroEngine, mock_log: MagicMock) -> None:
        engine.stop()
        stop_calls = [
            c[0][0] for c in mock_log.add.call_args_list
            if "已停止" in c[0][0]
        ]
        assert len(stop_calls) >= 1

    def test_quick_stop_before_start(self, engine: MacroEngine) -> None:
        """Calling stop before start should not raise."""
        engine.stop()  # no-op, thread is None

    def test_stop_stops_within_half_second(
        self, engine: MacroEngine, loop_scheme: Scheme
    ) -> None:
        engine.start(loop_scheme)
        engine.stop()
        assert not engine.is_running
