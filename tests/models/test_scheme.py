from __future__ import annotations

import uuid
from dataclasses import FrozenInstanceError

import pytest

from models.action import Action
from models.enums import MouseButton
from models.scheme import Scheme


def _make_action_press(key: str, order: int) -> Action:
    return Action.key_press(key, order=order)


def _make_sample_actions(count: int = 3) -> tuple[Action, ...]:
    actions: list[Action] = []
    for i in range(count):
        actions.append(Action.key_press(f"F{i+1}", order=i))
    return tuple(actions)


# ═══════════════════════════════════════════════════════════════
# 03.1 — Scheme 创建与冻结
# ═══════════════════════════════════════════════════════════════


class TestSchemeCreation:
    """测试 Scheme 数据类的基本创建与冻结特性。"""

    def test_create_scheme_with_valid_fields(self) -> None:
        actions = (_make_action_press("Space", 0),)
        scheme = Scheme(
            id=uuid.uuid4().hex,
            name="测试方案",
            description="用于测试的方案",
            actions=actions,
            loop=True,
            start_hotkey="F10",
            stop_hotkey="F12",
            is_preset=False,
        )
        assert scheme.name == "测试方案"
        assert scheme.description == "用于测试的方案"
        assert scheme.actions == actions
        assert scheme.loop is True
        assert scheme.start_hotkey == "F10"
        assert scheme.stop_hotkey == "F12"
        assert scheme.is_preset is False

    def test_default_field_values(self) -> None:
        actions = (_make_action_press("A", 0),)
        scheme = Scheme(
            id=uuid.uuid4().hex,
            name="默认值测试",
            description="",
            actions=actions,
        )
        assert scheme.loop is True
        assert scheme.start_hotkey == "F10"
        assert scheme.stop_hotkey == "F12"
        assert scheme.is_preset is False

    def test_scheme_with_multiple_actions(self) -> None:
        actions = (
            Action.key_press("Space", order=0, duration=0.1),
            Action.mouse_click(MouseButton.LEFT, order=1),
            Action.wait_random(10.0, 12.0, order=2),
        )
        scheme = Scheme(
            id=uuid.uuid4().hex,
            name="多步骤方案",
            description="包含不同类型操作",
            actions=actions,
        )
        assert len(scheme.actions) == 3
        assert scheme.actions[0].key == "Space"
        assert scheme.actions[1].mouse_button == MouseButton.LEFT
        assert scheme.actions[2].wait_min == 10.0

    def test_frozen_prevents_attribute_modification(self) -> None:
        actions = (_make_action_press("Space", 0),)
        scheme = Scheme(
            id=uuid.uuid4().hex,
            name="冻结测试",
            description="",
            actions=actions,
        )
        with pytest.raises(FrozenInstanceError):
            scheme.name = "修改后的名称"  # type: ignore[misc]

    def test_frozen_prevents_id_modification(self) -> None:
        actions = (_make_action_press("Space", 0),)
        scheme = Scheme(
            id=uuid.uuid4().hex,
            name="ID 冻结测试",
            description="",
            actions=actions,
        )
        with pytest.raises(FrozenInstanceError):
            scheme.id = "new-id"  # type: ignore[misc]

    def test_hashable_when_frozen(self) -> None:
        """冻结数据类应可哈希，可放入 set。"""
        actions = (_make_action_press("Space", 0),)
        sid = uuid.uuid4().hex
        s1 = Scheme(id=sid, name="哈希测试", description="", actions=actions)
        s2 = Scheme(id=sid, name="哈希测试", description="", actions=actions)
        s = {s1, s2}
        assert len(s) == 1

    def test_preset_scheme_skips_uuid_validation(self) -> None:
        """预设方案使用非 UUID 格式的 ID 不会触发验证错误。"""
        actions = (_make_action_press("4", 0),)
        scheme = Scheme(
            id="preset_zha_yu",
            name="炸鱼",
            description="炸鱼方案",
            actions=actions,
            is_preset=True,
        )
        assert scheme.id == "preset_zha_yu"
        assert scheme.is_preset is True


# ═══════════════════════════════════════════════════════════════
# 03.2 — __post_init__ 验证
# ═══════════════════════════════════════════════════════════════


class TestSchemeValidation:
    """测试 Scheme.__post_init__ 的所有验证规则。"""

    def test_name_cannot_be_empty(self) -> None:
        actions = (_make_action_press("A", 0),)
        with pytest.raises(ValueError, match="name"):
            Scheme(
                id=uuid.uuid4().hex,
                name="",
                description="",
                actions=actions,
            )

    def test_name_cannot_be_whitespace_only(self) -> None:
        actions = (_make_action_press("A", 0),)
        with pytest.raises(ValueError, match="name"):
            Scheme(
                id=uuid.uuid4().hex,
                name="   ",
                description="",
                actions=actions,
            )

    def test_actions_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError, match="actions"):
            Scheme(
                id=uuid.uuid4().hex,
                name="空 actions",
                description="",
                actions=(),
            )

    def test_start_hotkey_cannot_equal_stop_hotkey(self) -> None:
        actions = (_make_action_press("A", 0),)
        with pytest.raises(ValueError, match=r"start_hotkey.*stop_hotkey"):
            Scheme(
                id=uuid.uuid4().hex,
                name="热键冲突",
                description="",
                actions=actions,
                start_hotkey="F10",
                stop_hotkey="F10",
            )

    def test_non_preset_id_must_be_valid_uuid(self) -> None:
        actions = (_make_action_press("A", 0),)
        with pytest.raises(ValueError, match="UUID4"):
            Scheme(
                id="not-a-uuid",
                name="非法 ID",
                description="",
                actions=actions,
            )

    def test_non_preset_id_must_be_uuid_version_4(self) -> None:
        """非 UUID4 版本（如 UUID1）应被拒绝。"""
        actions = (_make_action_press("A", 0),)
        uid1 = uuid.uuid1().hex
        with pytest.raises(ValueError, match="UUID4"):
            Scheme(
                id=uid1,
                name="UUID1 版本",
                description="",
                actions=actions,
            )

    def test_non_preset_id_empty_string_rejected(self) -> None:
        actions = (_make_action_press("A", 0),)
        with pytest.raises(ValueError, match="UUID4"):
            Scheme(
                id="",
                name="空 ID",
                description="",
                actions=actions,
            )

    def test_non_preset_id_wrong_length_rejected(self) -> None:
        actions = (_make_action_press("A", 0),)
        with pytest.raises(ValueError, match="UUID4"):
            Scheme(
                id="a" * 16,
                name="短 ID",
                description="",
                actions=actions,
            )

    def test_non_preset_id_non_hex_rejected(self) -> None:
        actions = (_make_action_press("A", 0),)
        with pytest.raises(ValueError, match="UUID4"):
            Scheme(
                id="g" * 32,
                name="非法十六进制",
                description="",
                actions=actions,
            )

    def test_preset_skips_id_format_validation(self) -> None:
        """预设方案使用任意 ID 均不应触发 UUID 格式验证。"""
        actions = (_make_action_press("4", 0),)
        scheme = Scheme(
            id="any-random-preset-id-123",
            name="预设任意 ID",
            description="",
            actions=actions,
            is_preset=True,
        )
        assert scheme.id == "any-random-preset-id-123"


# ═══════════════════════════════════════════════════════════════
# 03.3 — create() 工厂方法
# ═══════════════════════════════════════════════════════════════


class TestSchemeCreateFactory:
    """测试 Scheme.create() 工厂类方法。"""

    def test_create_basic(self) -> None:
        actions = _make_sample_actions(2)
        scheme = Scheme.create(
            name="自定义方案",
            description="工厂创建",
            actions=actions,
        )
        assert scheme.name == "自定义方案"
        assert scheme.description == "工厂创建"
        assert scheme.actions == actions
        assert scheme.is_preset is False
        assert scheme.loop is True
        assert scheme.start_hotkey == "F10"
        assert scheme.stop_hotkey == "F12"

    def test_create_generates_unique_ids(self) -> None:
        actions = _make_sample_actions(1)
        s1 = Scheme.create(name="方案A", description="", actions=actions)
        s2 = Scheme.create(name="方案B", description="", actions=actions)
        assert s1.id != s2.id
        # 验证两个 ID 均为合法 UUID4
        for scheme in (s1, s2):
            uid = uuid.UUID(scheme.id)
            assert uid.version == 4

    def test_create_id_is_hex_string(self) -> None:
        actions = _make_sample_actions(1)
        scheme = Scheme.create(name="测试", description="", actions=actions)
        assert isinstance(scheme.id, str)
        assert len(scheme.id) == 32
        assert all(c in "0123456789abcdef" for c in scheme.id)

    def test_create_with_custom_hotkeys(self) -> None:
        actions = _make_sample_actions(1)
        scheme = Scheme.create(
            name="自定义热键",
            description="",
            actions=actions,
            start_hotkey="F1",
            stop_hotkey="F8",
        )
        assert scheme.start_hotkey == "F1"
        assert scheme.stop_hotkey == "F8"

    def test_create_with_custom_loop(self) -> None:
        actions = _make_sample_actions(1)
        scheme = Scheme.create(
            name="单次执行",
            description="",
            actions=actions,
            loop=False,
        )
        assert scheme.loop is False

    def test_create_passes_validation(self) -> None:
        """工厂方法产出的 Scheme 应通过 __post_init__ 验证。"""
        actions = _make_sample_actions(3)
        scheme = Scheme.create(name="验证通过", description="", actions=actions)
        assert scheme.name == "验证通过"

    def test_create_with_diverse_actions(self) -> None:
        """包含多种操作类型的方案创建。"""
        actions: tuple[Action, ...] = (
            Action.key_press("4", order=0),
            Action.wait_random(22.0, 24.0, order=1),
        )
        scheme = Scheme.create(
            name="炸鱼方案", description="炸鱼", actions=actions
        )
        assert len(scheme.actions) == 2


# ═══════════════════════════════════════════════════════════════
# 03.4 — create_preset() 工厂方法
# ═══════════════════════════════════════════════════════════════


class TestSchemeCreatePreset:
    """测试 Scheme.create_preset() 工厂类方法。"""

    def test_create_preset_basic(self) -> None:
        actions = _make_sample_actions(2)
        scheme = Scheme.create_preset(
            preset_id="preset_zha_yu",
            name="炸鱼",
            description="炸鱼方案",
            actions=actions,
        )
        assert scheme.id == "preset_zha_yu"
        assert scheme.name == "炸鱼"
        assert scheme.description == "炸鱼方案"
        assert scheme.is_preset is True
        assert scheme.loop is True
        assert scheme.start_hotkey == "F10"
        assert scheme.stop_hotkey == "F12"

    def test_create_preset_is_preset_true(self) -> None:
        actions = _make_sample_actions(1)
        scheme = Scheme.create_preset(
            preset_id="preset_clicker",
            name="连点器",
            description="",
            actions=actions,
        )
        assert scheme.is_preset is True

    def test_create_preset_preserves_provided_id(self) -> None:
        actions = _make_sample_actions(1)
        custom_id = "preset_xi_shuai"
        scheme = Scheme.create_preset(
            preset_id=custom_id,
            name="蟋蟀",
            description="",
            actions=actions,
        )
        assert scheme.id == custom_id

    def test_create_preset_with_custom_hotkeys(self) -> None:
        actions = _make_sample_actions(1)
        scheme = Scheme.create_preset(
            preset_id="preset_gather",
            name="自动采集",
            description="",
            actions=actions,
            start_hotkey="F5",
            stop_hotkey="F6",
        )
        assert scheme.start_hotkey == "F5"
        assert scheme.stop_hotkey == "F6"

    def test_create_preset_allows_non_uuid_id(self) -> None:
        """预设方案的 ID 可以是任意字符串，不受 UUID 验证约束。"""
        actions = _make_sample_actions(1)
        scheme = Scheme.create_preset(
            preset_id="some-prefixed-id_abc",
            name="任意 ID 预设",
            description="",
            actions=actions,
        )
        assert scheme.id == "some-prefixed-id_abc"
        assert scheme.is_preset is True


# ═══════════════════════════════════════════════════════════════
# 03.5 — to_dict / from_dict 往返序列化
# ═══════════════════════════════════════════════════════════════


class TestSchemeRoundtrip:
    """测试 Scheme.to_dict() 和 Scheme.from_dict() 往返序列化。"""

    def _make_five_action_scheme(self) -> Scheme:
        actions: tuple[Action, ...] = (
            Action.key_press("Space", order=0, duration=0.1),
            Action.mouse_click(MouseButton.LEFT, order=1, duration=0.05),
            Action.wait_fixed(5.0, order=2),
            Action.key_press("F", order=3, duration=0.5),
            Action.wait_random(10.0, 12.0, order=4),
        )
        return Scheme.create(
            name="往返测试方案",
            description="含 5 个操作步骤",
            actions=actions,
        )

    def test_roundtrip_preserves_all_fields(self) -> None:
        original = self._make_five_action_scheme()
        restored = Scheme.from_dict(original.to_dict())
        assert restored == original
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.description == original.description
        assert len(restored.actions) == len(original.actions)
        assert restored.loop == original.loop
        assert restored.start_hotkey == original.start_hotkey
        assert restored.stop_hotkey == original.stop_hotkey
        assert restored.is_preset == original.is_preset

    def test_roundtrip_preserves_is_preset(self) -> None:
        actions: tuple[Action, ...] = (
            Action.key_press("F", order=0),
            Action.wait_fixed(0.15, order=1),
        )
        original = Scheme.create_preset(
            preset_id="preset_clicker",
            name="连点器",
            description="连点器预设",
            actions=actions,
        )
        restored = Scheme.from_dict(original.to_dict())
        assert restored.is_preset is True
        assert restored.id == "preset_clicker"

    def test_roundtrip_preserves_id(self) -> None:
        actions = _make_sample_actions(2)
        original = Scheme.create(name="ID 保留", description="", actions=actions)
        restored = Scheme.from_dict(original.to_dict())
        assert restored.id == original.id

    def test_to_dict_actions_are_dicts(self) -> None:
        scheme = self._make_five_action_scheme()
        d = scheme.to_dict()
        assert isinstance(d["actions"], list)
        assert len(d["actions"]) == 5
        for action_dict in d["actions"]:
            assert isinstance(action_dict, dict)
            assert "action_type" in action_dict
            assert "order" in action_dict

    def test_to_dict_top_level_types(self) -> None:
        scheme = self._make_five_action_scheme()
        d = scheme.to_dict()
        assert isinstance(d["id"], str)
        assert isinstance(d["name"], str)
        assert isinstance(d["description"], str)
        assert isinstance(d["loop"], bool)
        assert isinstance(d["start_hotkey"], str)
        assert isinstance(d["stop_hotkey"], str)
        assert isinstance(d["is_preset"], bool)

    def test_roundtrip_nested_actions_fully_equal(self) -> None:
        original = self._make_five_action_scheme()
        restored = Scheme.from_dict(original.to_dict())
        for i, (orig_action, rest_action) in enumerate(
            zip(original.actions, restored.actions, strict=True)
        ):
            assert rest_action == orig_action, (
                f"Action[{i}] 不相等: {orig_action!r} vs {rest_action!r}"
            )

    def test_from_dict_preserves_all_action_types(self) -> None:
        """验证 from_dict 正确重建所有三种操作类型。"""
        scheme = self._make_five_action_scheme()
        restored = Scheme.from_dict(scheme.to_dict())
        action_types = [a.action_type.value for a in restored.actions]
        assert "key_press" in action_types
        assert "mouse_click" in action_types
        assert "wait" in action_types

    def test_roundtrip_with_zero_loop_preset(self) -> None:
        """is_preset=True + loop=False 的场景。"""
        actions = _make_sample_actions(1)
        original = Scheme.create_preset(
            preset_id="preset_single",
            name="单次预设",
            description="只运行一次",
            actions=actions,
            loop=False,
        )
        d = original.to_dict()
        assert d["loop"] is False
        assert d["is_preset"] is True
        restored = Scheme.from_dict(d)
        assert restored.loop is False
        assert restored.is_preset is True
        assert restored == original
