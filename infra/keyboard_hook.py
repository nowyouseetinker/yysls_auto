from __future__ import annotations

import contextlib
from collections.abc import Callable

import keyboard  # type: ignore[import-untyped]


def register_hotkey(key: str, callback: Callable[[], None]) -> None:
    """注册一个全局热键。

    封装 keyboard.add_hotkey()，在注册前验证参数有效性。

    Args:
        key: 热键字符串，如 "F10"、"ctrl+shift+a"。
        callback: 回调函数，触发时调用，无参数无返回值。

    Raises:
        TypeError: key 非 str 或 callback 不可调用。
        ValueError: key 为空字符串。
    """
    if not isinstance(key, str):
        raise TypeError(f"key must be str, got {type(key).__name__}")
    if not key:
        raise ValueError("key must be a non-empty string")
    if not callable(callback):
        raise TypeError(f"callback must be callable, got {type(callback).__name__}")

    keyboard.add_hotkey(key, callback)


def unregister_hotkey(key: str) -> None:
    """注销一个全局热键。

    封装 keyboard.remove_hotkey()。若热键未注册，则静默忽略（不抛异常）。

    Args:
        key: 热键字符串。

    Raises:
        TypeError: key 非 str。
        ValueError: key 为空字符串。
    """
    if not isinstance(key, str):
        raise TypeError(f"key must be str, got {type(key).__name__}")
    if not key:
        raise ValueError("key must be a non-empty string")

    with contextlib.suppress(KeyError):
        keyboard.remove_hotkey(key)


def clear_all() -> None:
    """注销所有全局热键。

    封装 keyboard.unhook_all_hotkeys()，移除所有已注册的热键。
    """
    keyboard.unhook_all_hotkeys()
