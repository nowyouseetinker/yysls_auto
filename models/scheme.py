from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass
from typing import Any

from models.action import Action
from models.enums import ActionType, MouseButton


@dataclass(frozen=True)
class Scheme:
    """方案数据类（不可变）。

    表示一套完整的游戏辅助操作方案，包含操作步骤序列、
    热键绑定、循环设置等配置。用户自定义方案使用 UUID4 标识，
    预设方案使用固定 ID（如 preset_zha_yu）。
    """

    id: str
    name: str
    description: str
    actions: tuple[Action, ...]
    loop: bool = True
    start_hotkey: str = "F10"
    stop_hotkey: str = "F12"
    is_preset: bool = False

    def __post_init__(self) -> None:
        """构造后验证字段合法性。"""
        if not self.name or not self.name.strip():
            raise ValueError("name 不能为空")

        if not self.actions:
            raise ValueError("actions 不能为空")

        if self.start_hotkey == self.stop_hotkey:
            raise ValueError(
                f"start_hotkey 与 stop_hotkey 不能相同: {self.start_hotkey!r}"
            )

        if not self.is_preset:
            try:
                uid = uuid.UUID(self.id)
            except (ValueError, AttributeError):
                raise ValueError(
                    f"非预设方案的 id 需为合法 UUID4 格式，实际值: {self.id!r}"
                ) from None
            if uid.version != 4:
                raise ValueError(
                    f"非预设方案的 id 需为 UUID4，实际 version={uid.version}: {self.id!r}"
                )

    # ── 工厂方法 ──────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        actions: tuple[Action, ...],
        loop: bool = True,
        start_hotkey: str = "F10",
        stop_hotkey: str = "F12",
    ) -> Scheme:
        """创建用户自定义方案（自动生成 UUID4 ID）。

        Args:
            name: 方案名称
            description: 方案描述
            actions: 操作步骤元组（非空）
            loop: 是否循环执行
            start_hotkey: 启动热键
            stop_hotkey: 停止热键
        """
        return cls(
            id=uuid.uuid4().hex,
            name=name,
            description=description,
            actions=actions,
            loop=loop,
            start_hotkey=start_hotkey,
            stop_hotkey=stop_hotkey,
            is_preset=False,
        )

    @classmethod
    def create_preset(
        cls,
        preset_id: str,
        name: str,
        description: str,
        actions: tuple[Action, ...],
        loop: bool = True,
        start_hotkey: str = "F10",
        stop_hotkey: str = "F12",
    ) -> Scheme:
        """创建预设方案（使用固定预设 ID）。

        Args:
            preset_id: 预设标识符（如 "preset_zha_yu"）
            name: 方案名称
            description: 方案描述
            actions: 操作步骤元组（非空）
            loop: 是否循环执行
            start_hotkey: 启动热键
            stop_hotkey: 停止热键
        """
        return cls(
            id=preset_id,
            name=name,
            description=description,
            actions=actions,
            loop=loop,
            start_hotkey=start_hotkey,
            stop_hotkey=stop_hotkey,
            is_preset=True,
        )

    # ── 序列化 ────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """转为 JSON 兼容字典（actions 嵌套序列化）。"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "actions": [a.to_dict() for a in self.actions],
            "loop": self.loop,
            "start_hotkey": self.start_hotkey,
            "stop_hotkey": self.stop_hotkey,
            "is_preset": self.is_preset,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Scheme:
        """从 to_dict() 输出的字典重建 Scheme。"""
        actions = tuple(Action.from_dict(a) for a in d["actions"])
        return cls(
            id=d["id"],
            name=d["name"],
            description=d["description"],
            actions=actions,
            loop=bool(d["loop"]),
            start_hotkey=d["start_hotkey"],
            stop_hotkey=d["stop_hotkey"],
            is_preset=bool(d["is_preset"]),
        )

    # ── 导入/导出（紧凑格式） ─────────────────────────────────

    @staticmethod
    def _action_to_compact(action: Action) -> dict[str, Any]:
        """将单个 Action 编码为紧凑字典（短键名，省略默认值）。"""
        out: dict[str, Any] = {}
        if action.action_type == ActionType.KEY_PRESS:
            out["t"] = 0
            out["k"] = action.key
            if abs(action.duration - 0.1) > 0.001:
                out["d"] = round(action.duration, 3)
        elif action.action_type == ActionType.MOUSE_CLICK:
            out["t"] = 1
            out["m"] = 0 if action.mouse_button == MouseButton.LEFT else 1
            if abs(action.duration - 0.1) > 0.001:
                out["d"] = round(action.duration, 3)
        elif action.action_type == ActionType.WAIT:
            if action.wait_seconds is not None:
                out["t"] = 2
                out["s"] = action.wait_seconds
            else:
                out["t"] = 3
                out["n"] = action.wait_min
                out["x"] = action.wait_max
        return out

    @staticmethod
    def _action_from_compact(d: dict[str, Any], order: int) -> Action:
        """从紧凑字典重建 Action（由 :meth:`_action_to_compact` 产生）。"""
        t = d["t"]
        if t == 0:  # KEY_PRESS
            return Action.key_press(
                key=d["k"],
                order=order,
                duration=d.get("d", 0.1),
            )
        elif t == 1:  # MOUSE_CLICK
            return Action.mouse_click(
                button=MouseButton.LEFT if d["m"] == 0 else MouseButton.RIGHT,
                order=order,
                duration=d.get("d", 0.1),
            )
        elif t == 2:  # WAIT fixed
            return Action.wait_fixed(seconds=d["s"], order=order)
        else:  # t == 3, WAIT random
            return Action.wait_random(min_s=d["n"], max_s=d["x"], order=order)

    def to_export_string(self) -> str:
        """将方案编码为紧凑 base64 字符串（短键名，省略默认值）。

        ``order`` 不参与编码——导入时从数组索引重建。

        Returns:
            纯 ASCII base64 字符串，可直接复制分享。
        """
        actions_compact = [self._action_to_compact(a) for a in self.actions]
        out: dict[str, Any] = {"n": self.name, "a": actions_compact}
        if self.description:
            out["d"] = self.description
        if not self.loop:
            out["l"] = 0
        if self.start_hotkey != "F10":
            out["sh"] = self.start_hotkey
        if self.stop_hotkey != "F12":
            out["st"] = self.stop_hotkey

        raw = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
        return base64.b64encode(raw.encode("utf-8")).decode("ascii")

    @classmethod
    def from_export_string(cls, export_str: str) -> Scheme:
        """从 ``to_export_string()`` 的输出还原并创建新方案（新 UUID）。

        Args:
            export_str: 紧凑格式的 base64 导出字符串。

        Returns:
            全新 :class:`Scheme`（新 UUID、非预设）。

        Raises:
            ValueError: 字符串格式无效、解码失败或缺少必要字段。
        """
        try:
            raw = base64.b64decode(export_str.encode("ascii")).decode("utf-8")
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("导入字符串格式无效，请检查复制内容") from exc

        name = data.get("n")
        if not name:
            raise ValueError("导入数据缺少方案名称")
        actions_raw = data.get("a")
        if not actions_raw:
            raise ValueError("方案至少需要一个操作步骤")

        actions = tuple(
            cls._action_from_compact(a, i) for i, a in enumerate(actions_raw)
        )

        return cls.create(
            name=name,
            description=data.get("d", ""),
            actions=actions,
            loop=data.get("l", 1) != 0,
            start_hotkey=data.get("sh", "F10"),
            stop_hotkey=data.get("st", "F12"),
        )
