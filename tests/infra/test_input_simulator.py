from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, call, patch

import pytest

from infra.input_simulator import click_mouse, interruptible_sleep, press_key
from models.enums import MouseButton


class TestPressKey:
    """press_key 函数的测试。"""

    @patch("infra.input_simulator.pydirectinput")
    @patch("infra.input_simulator.time.sleep")
    def test_calls_pydirectinput_in_correct_order(
        self, mock_sleep: MagicMock, mock_pydi: MagicMock
    ) -> None:
        press_key("a", duration=0.2)

        assert mock_pydi.keyDown.call_args_list == [call("a")]
        mock_sleep.assert_called_once_with(0.2)
        assert mock_pydi.keyUp.call_args_list == [call("a")]

    @patch("infra.input_simulator.pydirectinput")
    @patch("infra.input_simulator.time.sleep")
    def test_uses_default_duration(self, mock_sleep: MagicMock, mock_pydi: MagicMock) -> None:
        press_key("enter")

        mock_sleep.assert_called_once_with(0.1)

    def test_raises_on_empty_key(self) -> None:
        with pytest.raises(ValueError, match="key 不能为空字符串"):
            press_key("")

    def test_raises_on_negative_duration(self) -> None:
        with pytest.raises(ValueError, match="duration 必须 >= 0"):
            press_key("a", duration=-0.1)

    @patch("infra.input_simulator.pydirectinput")
    @patch("infra.input_simulator.time.sleep")
    def test_allows_zero_duration(self, mock_sleep: MagicMock, mock_pydi: MagicMock) -> None:
        press_key("space", duration=0.0)

        mock_sleep.assert_called_once_with(0.0)


class TestClickMouse:
    """click_mouse 函数的测试。"""

    @patch("infra.input_simulator.pydirectinput")
    @patch("infra.input_simulator.time.sleep")
    def test_calls_pydirectinput_for_left_click(
        self, mock_sleep: MagicMock, mock_pydi: MagicMock
    ) -> None:
        click_mouse(MouseButton.LEFT, duration=0.15)

        assert mock_pydi.mouseDown.call_args_list == [call(button=MouseButton.LEFT)]
        mock_sleep.assert_called_once_with(0.15)
        assert mock_pydi.mouseUp.call_args_list == [call(button=MouseButton.LEFT)]

    @patch("infra.input_simulator.pydirectinput")
    @patch("infra.input_simulator.time.sleep")
    def test_calls_pydirectinput_for_right_click(
        self, mock_sleep: MagicMock, mock_pydi: MagicMock
    ) -> None:
        click_mouse(MouseButton.RIGHT)

        assert mock_pydi.mouseDown.call_args_list == [call(button=MouseButton.RIGHT)]
        mock_sleep.assert_called_once_with(0.1)
        assert mock_pydi.mouseUp.call_args_list == [call(button=MouseButton.RIGHT)]

    @patch("infra.input_simulator.pydirectinput")
    @patch("infra.input_simulator.time.sleep")
    def test_uses_default_duration(self, mock_sleep: MagicMock, mock_pydi: MagicMock) -> None:
        click_mouse(MouseButton.LEFT)

        mock_sleep.assert_called_once_with(0.1)

    def test_raises_on_negative_duration(self) -> None:
        with pytest.raises(ValueError, match="duration 必须 >= 0"):
            click_mouse(MouseButton.LEFT, duration=-0.05)

    @patch("infra.input_simulator.pydirectinput")
    @patch("infra.input_simulator.time.sleep")
    def test_allows_zero_duration(self, mock_sleep: MagicMock, mock_pydi: MagicMock) -> None:
        click_mouse(MouseButton.LEFT, duration=0.0)

        mock_sleep.assert_called_once_with(0.0)


class TestInterruptibleSleep:
    """interruptible_sleep 函数的测试。"""

    @patch("infra.input_simulator.time.sleep")
    def test_sleeps_full_duration_when_not_interrupted(self, mock_sleep: MagicMock) -> None:
        stop_event = threading.Event()

        interruptible_sleep(1.0, stop_event, step=0.1)

        # 1.0s / 0.1 step = 10 calls to sleep(0.1)
        assert mock_sleep.call_count == 10
        mock_sleep.assert_has_calls([call(0.1)] * 10)

    @patch("infra.input_simulator.time.sleep")
    def test_returns_early_when_stop_event_is_set(self, mock_sleep: MagicMock) -> None:
        stop_event = threading.Event()

        # Set the event after 3 sleep calls
        call_count = [0]

        def side_effect(seconds: float) -> None:
            call_count[0] += 1
            if call_count[0] >= 3:
                stop_event.set()

        mock_sleep.side_effect = side_effect

        interruptible_sleep(2.0, stop_event, step=0.1)

        # Should have called sleep 3 times before returning
        assert mock_sleep.call_count == 3

    def test_returns_immediately_for_zero_duration(self) -> None:
        stop_event = threading.Event()

        start = time.perf_counter()
        interruptible_sleep(0.0, stop_event)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.01  # Should return nearly instantly

    @patch("infra.input_simulator.time.sleep")
    def test_checks_stop_event_before_first_sleep(self, mock_sleep: MagicMock) -> None:
        stop_event = threading.Event()
        stop_event.set()

        interruptible_sleep(5.0, stop_event)

        mock_sleep.assert_not_called()

    def test_raises_on_negative_total_seconds(self) -> None:
        stop_event = threading.Event()
        with pytest.raises(ValueError, match="total_seconds 必须 >= 0"):
            interruptible_sleep(-1.0, stop_event)

    def test_raises_on_zero_or_negative_step(self) -> None:
        stop_event = threading.Event()
        with pytest.raises(ValueError, match="step 必须 > 0"):
            interruptible_sleep(1.0, stop_event, step=0.0)
        with pytest.raises(ValueError, match="step 必须 > 0"):
            interruptible_sleep(1.0, stop_event, step=-0.1)

    @patch("infra.input_simulator.time.sleep")
    def test_handles_partial_final_step(self, mock_sleep: MagicMock) -> None:
        """当 total_seconds 不是 step 的整数倍时，最后一步应只睡眠剩余时间。"""
        stop_event = threading.Event()

        interruptible_sleep(0.25, stop_event, step=0.1)

        # 0.25 / 0.1: two full steps of 0.1, one partial step of ~0.05 = 3 calls
        assert mock_sleep.call_count == 3
        slept = [c.args[0] for c in mock_sleep.call_args_list]
        assert slept[0] == pytest.approx(0.1)
        assert slept[1] == pytest.approx(0.1)
        assert slept[2] == pytest.approx(0.05)
