from __future__ import annotations

import threading
import time

import pydirectinput  # type: ignore[import-untyped]

from models.enums import MouseButton


def press_key(key: str, duration: float = 0.1) -> None:
    """模拟按键：按下、持续、释放。

    Args:
        key: 按键名称，不可为空字符串。
        duration: 按下持续时间（秒），必须 >= 0。

    Raises:
        ValueError: 如果 key 为空或 duration < 0。
    """
    if not key:
        raise ValueError("key 不能为空字符串")
    if duration < 0:
        raise ValueError(f"duration 必须 >= 0，实际: {duration}")

    # pydirectinput's KEYBOARD_MAPPING uses lowercase for letters and
    # named keys (e.g. 'f', 'space').  Normalise so both "F" and "f" work.
    normalized_key = key.lower()
    pydirectinput.keyDown(normalized_key)
    time.sleep(duration)
    pydirectinput.keyUp(normalized_key)


def click_mouse(button: MouseButton, duration: float = 0.1) -> None:
    """模拟鼠标点击：按下、持续、释放。

    Args:
        button: 鼠标按钮（MouseButton.LEFT 或 MouseButton.RIGHT）。
        duration: 按下持续时间（秒），必须 >= 0。

    Raises:
        ValueError: 如果 duration < 0。
    """
    if duration < 0:
        raise ValueError(f"duration 必须 >= 0，实际: {duration}")

    pydirectinput.mouseDown(button=button)
    time.sleep(duration)
    pydirectinput.mouseUp(button=button)


def interruptible_sleep(
    total_seconds: float,
    stop_event: threading.Event,
    step: float = 0.1,
) -> None:
    """可中断的睡眠：以 step 秒为步长分片睡眠，允许通过 stop_event 提前返回。

    总睡眠时间约为 total_seconds（最多多出一个 step 的精度误差）。
    如果 stop_event 在睡眠期间被 set，则立即返回。

    Args:
        total_seconds: 总睡眠时长（秒），必须 >= 0。
        stop_event: 用于提前中断的 threading.Event。
        step: 每次检查的间隔步长（秒），默认 0.1。

    Raises:
        ValueError: 如果 total_seconds < 0 或 step <= 0。
    """
    if total_seconds < 0:
        raise ValueError(f"total_seconds 必须 >= 0，实际: {total_seconds}")
    if step <= 0:
        raise ValueError(f"step 必须 > 0，实际: {step}")

    elapsed = 0.0
    while total_seconds - elapsed > 1e-9:
        if stop_event.is_set():
            return
        remaining = total_seconds - elapsed
        chunk = min(step, remaining)
        time.sleep(chunk)
        elapsed += chunk
