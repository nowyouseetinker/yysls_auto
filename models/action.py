from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.enums import ActionType, MouseButton


@dataclass(frozen=True)
class Action:
    """操作步骤数据类（不可变）。

    表示游戏辅助操作序列中的单个步骤，可以是按键、鼠标点击或等待。
    使用工厂类方法构造，创建后不可修改。
    """

    action_type: ActionType
    order: int
    key: str | None = None
    mouse_button: MouseButton | None = None
    duration: float = 0.1
    wait_seconds: float | None = None
    wait_min: float | None = None
    wait_max: float | None = None

    def __post_init__(self) -> None:
        """构造后验证字段合法性。"""
        if self.order < 0:
            raise ValueError(f"order 必须 >= 0，实际值 {self.order}")
        if self.duration < 0:
            raise ValueError(f"duration 必须 >= 0，实际值 {self.duration}")

        if self.action_type == ActionType.KEY_PRESS:
            if self.key is None:
                raise ValueError("KEY_PRESS 操作必须提供 key")
            if self.mouse_button is not None:
                raise ValueError("KEY_PRESS 操作不能设置 mouse_button")

        elif self.action_type == ActionType.MOUSE_CLICK:
            if self.mouse_button is None:
                raise ValueError("MOUSE_CLICK 操作必须提供 mouse_button")
            if self.key is not None:
                raise ValueError("MOUSE_CLICK 操作不能设置 key")

        elif self.action_type == ActionType.WAIT:
            if self.key is not None:
                raise ValueError("WAIT 操作不能设置 key")
            if self.mouse_button is not None:
                raise ValueError("WAIT 操作不能设置 mouse_button")
            has_fixed = self.wait_seconds is not None
            has_random = self.wait_min is not None and self.wait_max is not None
            if has_fixed and has_random:
                raise ValueError(
                    "WAIT 操作不能同时设置 wait_seconds 和 wait_min/wait_max"
                )
            part_random = (self.wait_min is None) != (self.wait_max is None)
            if part_random:
                raise ValueError("WAIT 操作必须同时设置 wait_min 和 wait_max")
            if not has_fixed and not has_random:
                raise ValueError(
                    "WAIT 操作必须设置 wait_seconds 或 (wait_min 和 wait_max)"
                )

    # ── 工厂方法 ──────────────────────────────────────────────

    @classmethod
    def key_press(cls, key: str, order: int, duration: float = 0.1) -> Action:
        """创建键盘按键操作。

        Args:
            key: 按键名（如 "Space"、"F"、"1"）
            order: 步骤序号
            duration: 按下持续时间（秒）
        """
        return cls(
            action_type=ActionType.KEY_PRESS,
            key=key,
            order=order,
            duration=duration,
        )

    @classmethod
    def mouse_click(
        cls, button: MouseButton, order: int, duration: float = 0.1
    ) -> Action:
        """创建鼠标点击操作。

        Args:
            button: 鼠标按钮（左键/右键）
            order: 步骤序号
            duration: 点击持续时间（秒）
        """
        return cls(
            action_type=ActionType.MOUSE_CLICK,
            mouse_button=button,
            order=order,
            duration=duration,
        )

    @classmethod
    def wait_fixed(cls, seconds: float, order: int) -> Action:
        """创建固定时长的等待操作。

        Args:
            seconds: 等待秒数
            order: 步骤序号
        """
        return cls(
            action_type=ActionType.WAIT,
            wait_seconds=seconds,
            order=order,
        )

    @classmethod
    def wait_random(cls, min_s: float, max_s: float, order: int) -> Action:
        """创建随机时长的等待操作。

        Args:
            min_s: 最小等待秒数
            max_s: 最大等待秒数
            order: 步骤序号

        Raises:
            ValueError: 若 min_s > max_s
        """
        if min_s > max_s:
            raise ValueError(f"min_s ({min_s}) 必须 <= max_s ({max_s})")
        return cls(
            action_type=ActionType.WAIT,
            wait_min=min_s,
            wait_max=max_s,
            order=order,
        )

    # ── 显示 ──────────────────────────────────────────────────

    def __str__(self) -> str:
        """返回中文可读描述。"""
        if self.action_type == ActionType.KEY_PRESS:
            return f"按键 {self.key} ({self.duration}s)"
        elif self.action_type == ActionType.MOUSE_CLICK:
            button_cn = "左键" if self.mouse_button == MouseButton.LEFT else "右键"
            return f"鼠标{button_cn}点击 ({self.duration}s)"
        else:  # ActionType.WAIT
            if self.wait_seconds is not None:
                return f"等待 {self.wait_seconds} 秒"
            else:
                return f"等待 {self.wait_min}~{self.wait_max} 秒"

    # ── 序列化 ────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """转为 JSON 兼容字典（枚举转字符串，保留 None）。"""
        return {
            "action_type": self.action_type.value,
            "order": self.order,
            "key": self.key,
            "mouse_button": self.mouse_button.value if self.mouse_button is not None else None,
            "duration": self.duration,
            "wait_seconds": self.wait_seconds,
            "wait_min": self.wait_min,
            "wait_max": self.wait_max,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Action:
        """从 to_dict() 输出的字典重建 Action。"""
        mouse_button_raw = d.get("mouse_button")
        return cls(
            action_type=ActionType(d["action_type"]),
            order=int(d["order"]),
            key=d.get("key"),
            mouse_button=MouseButton(mouse_button_raw) if mouse_button_raw is not None else None,
            duration=float(d.get("duration", 0.1)),
            wait_seconds=d.get("wait_seconds"),
            wait_min=d.get("wait_min"),
            wait_max=d.get("wait_max"),
        )
