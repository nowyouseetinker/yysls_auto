from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from models.action import Action
from models.enums import ActionType, MouseButton

# ═══════════════════════════════════════════════════════════════
# 02.1 — Action 创建与冻结
# ═══════════════════════════════════════════════════════════════


class TestActionCreation:
    """测试 Action 数据类的基本创建与冻结特性。"""

    def test_create_key_press_action(self) -> None:
        action = Action(
            action_type=ActionType.KEY_PRESS,
            order=0,
            key="Space",
            duration=0.1,
        )
        assert action.action_type == ActionType.KEY_PRESS
        assert action.order == 0
        assert action.key == "Space"
        assert action.mouse_button is None
        assert action.duration == 0.1
        assert action.wait_seconds is None
        assert action.wait_min is None
        assert action.wait_max is None

    def test_create_mouse_click_action(self) -> None:
        action = Action(
            action_type=ActionType.MOUSE_CLICK,
            order=1,
            mouse_button=MouseButton.LEFT,
            duration=0.05,
        )
        assert action.action_type == ActionType.MOUSE_CLICK
        assert action.mouse_button == MouseButton.LEFT
        assert action.key is None
        assert action.duration == 0.05

    def test_create_wait_fixed_action(self) -> None:
        action = Action(
            action_type=ActionType.WAIT,
            order=2,
            wait_seconds=5.0,
        )
        assert action.action_type == ActionType.WAIT
        assert action.wait_seconds == 5.0
        assert action.wait_min is None
        assert action.wait_max is None
        assert action.key is None
        assert action.mouse_button is None

    def test_create_wait_random_action(self) -> None:
        action = Action(
            action_type=ActionType.WAIT,
            order=3,
            wait_min=10.0,
            wait_max=12.0,
        )
        assert action.wait_min == 10.0
        assert action.wait_max == 12.0
        assert action.wait_seconds is None

    def test_default_duration(self) -> None:
        action = Action(action_type=ActionType.WAIT, order=0, wait_seconds=1.0)
        assert action.duration == 0.1

    def test_frozen_prevents_attribute_modification(self) -> None:
        action = Action(action_type=ActionType.KEY_PRESS, order=0, key="A")
        with pytest.raises(FrozenInstanceError):
            action.order = 999  # type: ignore[misc]

    def test_hashable_when_frozen(self) -> None:
        """冻结数据类应可哈希，可放入 set。"""
        a1 = Action(action_type=ActionType.KEY_PRESS, order=0, key="A")
        a2 = Action(action_type=ActionType.KEY_PRESS, order=0, key="A")
        s = {a1, a2}
        assert len(s) == 1


# ═══════════════════════════════════════════════════════════════
# 02.2 — __post_init__ 验证
# ═══════════════════════════════════════════════════════════════


class TestActionValidation:
    """测试 Action.__post_init__ 的所有验证规则。"""

    # ── 通用约束 ──

    def test_order_must_be_non_negative(self) -> None:
        with pytest.raises(ValueError, match="order"):
            Action(action_type=ActionType.KEY_PRESS, order=-1, key="A")

    def test_order_zero_is_valid(self) -> None:
        action = Action(action_type=ActionType.KEY_PRESS, order=0, key="A")
        assert action.order == 0

    def test_duration_must_be_non_negative(self) -> None:
        with pytest.raises(ValueError, match="duration"):
            Action(action_type=ActionType.KEY_PRESS, order=0, key="A", duration=-0.1)

    def test_duration_zero_is_valid(self) -> None:
        action = Action(action_type=ActionType.KEY_PRESS, order=0, key="A", duration=0.0)
        assert action.duration == 0.0

    # ── KEY_PRESS 约束 ──

    def test_key_press_requires_key(self) -> None:
        with pytest.raises(ValueError, match="KEY_PRESS.*key"):
            Action(action_type=ActionType.KEY_PRESS, order=0)

    def test_key_press_rejects_mouse_button(self) -> None:
        with pytest.raises(ValueError, match="KEY_PRESS.*mouse_button"):
            Action(
                action_type=ActionType.KEY_PRESS,
                order=0,
                key="A",
                mouse_button=MouseButton.LEFT,
            )

    # ── MOUSE_CLICK 约束 ──

    def test_mouse_click_requires_mouse_button(self) -> None:
        with pytest.raises(ValueError, match="MOUSE_CLICK.*mouse_button"):
            Action(action_type=ActionType.MOUSE_CLICK, order=0)

    def test_mouse_click_rejects_key(self) -> None:
        with pytest.raises(ValueError, match="MOUSE_CLICK.*key"):
            Action(
                action_type=ActionType.MOUSE_CLICK,
                order=0,
                mouse_button=MouseButton.LEFT,
                key="A",
            )

    # ── WAIT 约束 ──

    def test_wait_requires_wait_seconds_or_wait_min_max(self) -> None:
        with pytest.raises(ValueError, match="WAIT.*wait_seconds.*wait_min.*wait_max"):
            Action(action_type=ActionType.WAIT, order=0)

    def test_wait_cannot_have_both_fixed_and_random(self) -> None:
        with pytest.raises(ValueError, match="同时"):
            Action(
                action_type=ActionType.WAIT,
                order=0,
                wait_seconds=5.0,
                wait_min=1.0,
                wait_max=10.0,
            )

    def test_wait_random_requires_both_min_and_max(self) -> None:
        with pytest.raises(ValueError, match="同时"):
            Action(action_type=ActionType.WAIT, order=0, wait_min=5.0)

    def test_wait_random_requires_both_max_and_min(self) -> None:
        with pytest.raises(ValueError, match="同时"):
            Action(action_type=ActionType.WAIT, order=0, wait_max=10.0)

    def test_wait_rejects_key(self) -> None:
        with pytest.raises(ValueError, match="WAIT.*key"):
            Action(action_type=ActionType.WAIT, order=0, wait_seconds=1.0, key="A")

    def test_wait_rejects_mouse_button(self) -> None:
        with pytest.raises(ValueError, match="WAIT.*mouse_button"):
            Action(
                action_type=ActionType.WAIT,
                order=0,
                wait_seconds=1.0,
                mouse_button=MouseButton.LEFT,
            )


# ═══════════════════════════════════════════════════════════════
# 02.3 — key_press 工厂方法
# ═══════════════════════════════════════════════════════════════


class TestKeyPressFactory:
    """测试 Action.key_press() 工厂类方法。"""

    def test_basic_key_press(self) -> None:
        action = Action.key_press("Space", order=0)
        assert action.action_type == ActionType.KEY_PRESS
        assert action.key == "Space"
        assert action.order == 0
        assert action.duration == 0.1
        assert action.mouse_button is None

    def test_key_press_with_custom_duration(self) -> None:
        action = Action.key_press("F", order=5, duration=0.5)
        assert action.key == "F"
        assert action.duration == 0.5
        assert action.order == 5

    def test_key_press_passes_validation(self) -> None:
        """工厂方法产出的 Action 应通过 __post_init__ 验证。"""
        action = Action.key_press("1", order=0)
        assert action.key == "1"
        assert action.action_type == ActionType.KEY_PRESS

    def test_key_press_with_invalid_order_raises(self) -> None:
        with pytest.raises(ValueError):
            Action.key_press("A", order=-1)


# ═══════════════════════════════════════════════════════════════
# 02.4 — mouse_click / wait_fixed 工厂方法
# ═══════════════════════════════════════════════════════════════


class TestMouseClickFactory:
    """测试 Action.mouse_click() 工厂类方法。"""

    def test_left_click(self) -> None:
        action = Action.mouse_click(MouseButton.LEFT, order=1)
        assert action.action_type == ActionType.MOUSE_CLICK
        assert action.mouse_button == MouseButton.LEFT
        assert action.order == 1
        assert action.duration == 0.1
        assert action.key is None

    def test_right_click(self) -> None:
        action = Action.mouse_click(MouseButton.RIGHT, order=2, duration=0.2)
        assert action.mouse_button == MouseButton.RIGHT
        assert action.duration == 0.2

    def test_mouse_click_passes_validation(self) -> None:
        action = Action.mouse_click(MouseButton.LEFT, order=3)
        assert action.action_type == ActionType.MOUSE_CLICK

    def test_mouse_click_with_invalid_order_raises(self) -> None:
        with pytest.raises(ValueError):
            Action.mouse_click(MouseButton.LEFT, order=-1)


class TestWaitFixedFactory:
    """测试 Action.wait_fixed() 工厂类方法。"""

    def test_wait_fixed_basic(self) -> None:
        action = Action.wait_fixed(10.0, order=2)
        assert action.action_type == ActionType.WAIT
        assert action.wait_seconds == 10.0
        assert action.order == 2
        assert action.wait_min is None
        assert action.wait_max is None
        assert action.key is None
        assert action.mouse_button is None

    def test_wait_fixed_with_fractional_seconds(self) -> None:
        action = Action.wait_fixed(0.15, order=0)
        assert action.wait_seconds == 0.15

    def test_wait_fixed_passes_validation(self) -> None:
        action = Action.wait_fixed(5.0, order=0)
        assert action.wait_seconds == 5.0


# ═══════════════════════════════════════════════════════════════
# 02.5 — wait_random 工厂方法 与 __str__
# ═══════════════════════════════════════════════════════════════


class TestWaitRandomFactory:
    """测试 Action.wait_random() 工厂类方法。"""

    def test_wait_random_basic(self) -> None:
        action = Action.wait_random(22.0, 24.0, order=1)
        assert action.action_type == ActionType.WAIT
        assert action.wait_min == 22.0
        assert action.wait_max == 24.0
        assert action.wait_seconds is None
        assert action.key is None

    def test_wait_random_min_equals_max(self) -> None:
        """min_s == max_s 是合法的。"""
        action = Action.wait_random(5.0, 5.0, order=0)
        assert action.wait_min == 5.0
        assert action.wait_max == 5.0

    def test_wait_random_min_greater_than_max_raises(self) -> None:
        with pytest.raises(ValueError, match="min_s"):
            Action.wait_random(10.0, 5.0, order=0)

    def test_wait_random_passes_validation(self) -> None:
        action = Action.wait_random(1.0, 3.0, order=0)
        assert action.wait_min == 1.0
        assert action.wait_max == 3.0


class TestActionStr:
    """测试 Action.__str__ 中文描述输出。"""

    def test_key_press_str(self) -> None:
        action = Action.key_press("Space", order=0, duration=0.1)
        assert str(action) == "按键 Space (0.1s)"

    def test_key_press_str_custom_duration(self) -> None:
        action = Action.key_press("F", order=1, duration=0.5)
        assert str(action) == "按键 F (0.5s)"

    def test_mouse_left_click_str(self) -> None:
        action = Action.mouse_click(MouseButton.LEFT, order=0)
        assert str(action) == "鼠标左键点击 (0.1s)"

    def test_mouse_right_click_str(self) -> None:
        action = Action.mouse_click(MouseButton.RIGHT, order=1, duration=0.2)
        assert str(action) == "鼠标右键点击 (0.2s)"

    def test_wait_fixed_str(self) -> None:
        action = Action.wait_fixed(5.0, order=2)
        assert str(action) == "等待 5.0 秒"

    def test_wait_random_str(self) -> None:
        action = Action.wait_random(95.0, 105.0, order=3)
        assert str(action) == "等待 95.0~105.0 秒"

    def test_all_action_types_produce_readable_chinese(self) -> None:
        """验证三种操作类型均生成可读的中文字符串（非空、包含中文）。"""
        actions = [
            Action.key_press("Space", order=0),
            Action.mouse_click(MouseButton.LEFT, order=1),
            Action.wait_fixed(5.0, order=2),
            Action.wait_random(10.0, 12.0, order=3),
        ]
        for action in actions:
            s = str(action)
            assert s, f"__str__ 不应返回空字符串: {action}"
            assert any("一" <= c <= "鿿" for c in s), (
                f"__str__ 应包含中文字符: {s!r}"
            )


# ═══════════════════════════════════════════════════════════════
# 02.6 — to_dict / from_dict 往返序列化
# ═══════════════════════════════════════════════════════════════


class TestActionRoundtrip:
    """测试 Action.to_dict() 和 Action.from_dict() 往返序列化。"""

    def test_key_press_roundtrip(self) -> None:
        original = Action.key_press("Space", order=0, duration=0.1)
        d = original.to_dict()
        restored = Action.from_dict(d)
        assert restored == original
        assert restored.action_type == ActionType.KEY_PRESS
        assert restored.key == "Space"

    def test_mouse_click_roundtrip(self) -> None:
        original = Action.mouse_click(MouseButton.RIGHT, order=3, duration=0.15)
        d = original.to_dict()
        restored = Action.from_dict(d)
        assert restored == original
        assert restored.mouse_button == MouseButton.RIGHT

    def test_wait_fixed_roundtrip(self) -> None:
        original = Action.wait_fixed(10.0, order=1)
        d = original.to_dict()
        restored = Action.from_dict(d)
        assert restored == original
        assert restored.wait_seconds == 10.0

    def test_wait_random_roundtrip(self) -> None:
        original = Action.wait_random(22.0, 24.0, order=2)
        d = original.to_dict()
        restored = Action.from_dict(d)
        assert restored == original
        assert restored.wait_min == 22.0
        assert restored.wait_max == 24.0

    def test_to_dict_enums_are_strings(self) -> None:
        action = Action.key_press("Space", order=0)
        d = action.to_dict()
        assert isinstance(d["action_type"], str)
        assert d["action_type"] == "key_press"
        assert d["mouse_button"] is None

    def test_to_dict_preserves_none(self) -> None:
        action = Action.key_press("A", order=0)
        d = action.to_dict()
        assert d["mouse_button"] is None
        assert d["wait_seconds"] is None
        assert d["wait_min"] is None
        assert d["wait_max"] is None

    def test_mouse_click_to_dict_has_string_button(self) -> None:
        action = Action.mouse_click(MouseButton.LEFT, order=1)
        d = action.to_dict()
        assert d["mouse_button"] == "left"
        assert isinstance(d["mouse_button"], str)

    def test_roundtrip_preserves_equality_all_fields(self) -> None:
        """往返后所有字段保持相等。"""
        original = Action.wait_random(95.0, 105.0, order=4)
        restored = Action.from_dict(original.to_dict())
        assert restored.action_type == original.action_type
        assert restored.order == original.order
        assert restored.key == original.key
        assert restored.mouse_button == original.mouse_button
        assert restored.duration == original.duration
        assert restored.wait_seconds == original.wait_seconds
        assert restored.wait_min == original.wait_min
        assert restored.wait_max == original.wait_max

    def test_from_dict_with_default_duration(self) -> None:
        """传入的字典不含 duration 字段时应使用默认值 0.1。"""
        d = {
            "action_type": "key_press",
            "order": 0,
            "key": "A",
            "mouse_button": None,
            "wait_seconds": None,
            "wait_min": None,
            "wait_max": None,
        }
        action = Action.from_dict(d)
        assert action.duration == 0.1
