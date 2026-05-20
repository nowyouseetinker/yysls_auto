from __future__ import annotations

from models.action import Action
from models.enums import MouseButton
from models.scheme import Scheme

# ═══════════════════════════════════════════════════════════════════
# 预设方案 ID 常量
# ═══════════════════════════════════════════════════════════════════

PRESET_IDS = {
    "zha_yu": "preset_zha_yu",
    "xi_shuai": "preset_xi_shuai",
    "gather": "preset_gather",
    "clicker": "preset_clicker",
}


# ═══════════════════════════════════════════════════════════════════
# 预设方案构建函数（私有）
# ═══════════════════════════════════════════════════════════════════


def _build_preset_zha_yu() -> Scheme:
    """构建炸鱼预设方案：按键4 → 等22~24秒(随机) → 循环。"""
    actions: tuple[Action, ...] = (
        Action.key_press("4", order=0),
        Action.wait_random(22.0, 24.0, order=1),
    )
    return Scheme.create_preset(
        preset_id=PRESET_IDS["zha_yu"],
        name="炸鱼",
        description="按键4后等待22~24秒随机时长，循环执行",
        actions=actions,
    )


def _build_preset_xi_shuai() -> Scheme:
    """构建蟋蟀预设方案：左键 → 等100秒 → 空格 → 等5秒 → F → 等5秒 → 循环。"""
    actions: tuple[Action, ...] = (
        Action.mouse_click(MouseButton.LEFT, order=0),
        Action.wait_fixed(100.0, order=1),
        Action.key_press("Space", order=2),
        Action.wait_fixed(5.0, order=3),
        Action.key_press("F", order=4),
        Action.wait_fixed(5.0, order=5),
    )
    return Scheme.create_preset(
        preset_id=PRESET_IDS["xi_shuai"],
        name="蟋蟀",
        description="左键点击后等待100秒，按空格→等5秒→按F→等5秒，循环执行",
        actions=actions,
    )


def _build_preset_gather() -> Scheme:
    """构建自动采集预设方案：按键1 → 等10~12秒(随机) → 循环。"""
    actions: tuple[Action, ...] = (
        Action.key_press("1", order=0),
        Action.wait_random(10.0, 12.0, order=1),
    )
    return Scheme.create_preset(
        preset_id=PRESET_IDS["gather"],
        name="自动采集",
        description="按键1后等待10~12秒随机时长，循环执行",
        actions=actions,
    )


def _build_preset_clicker() -> Scheme:
    """构建连点器预设方案：F → 等0.15秒 → 循环。"""
    actions: tuple[Action, ...] = (
        Action.key_press("F", order=0),
        Action.wait_fixed(0.15, order=1),
    )
    return Scheme.create_preset(
        preset_id=PRESET_IDS["clicker"],
        name="连点器",
        description="按键F后等待0.15秒，循环执行",
        actions=actions,
    )


# ═══════════════════════════════════════════════════════════════════
# 模块级预设方案列表（只读，Scheme 本身为 frozen dataclass）
# ═══════════════════════════════════════════════════════════════════

_PRESETS: list[Scheme] = [
    _build_preset_zha_yu(),
    _build_preset_xi_shuai(),
    _build_preset_gather(),
    _build_preset_clicker(),
]

_PRESET_BY_ID: dict[str, Scheme] = {p.id: p for p in _PRESETS}


# ═══════════════════════════════════════════════════════════════════
# 公开 API
# ═══════════════════════════════════════════════════════════════════


def get_all_presets() -> list[Scheme]:
    """返回全部 4 套内置预设方案。

    Returns:
        预设 Scheme 列表（顺序固定：炸鱼、蟋蟀、自动采集、连点器）。
    """
    return list(_PRESETS)


def get_preset(preset_id: str) -> Scheme | None:
    """按预设 ID 查找方案。

    Args:
        preset_id: 预设标识符，如 "preset_zha_yu"。

    Returns:
        匹配的 Scheme 或 None（ID 不存在时）。
    """
    return _PRESET_BY_ID.get(preset_id)
