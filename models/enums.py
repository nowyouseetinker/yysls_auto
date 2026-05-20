from __future__ import annotations

from enum import StrEnum


class ActionType(StrEnum):
    """操作类型枚举：键盘按键、鼠标点击、等待。"""

    KEY_PRESS = "key_press"
    MOUSE_CLICK = "mouse_click"
    WAIT = "wait"


class MouseButton(StrEnum):
    """鼠标按钮枚举：左键、右键。"""

    LEFT = "left"
    RIGHT = "right"
