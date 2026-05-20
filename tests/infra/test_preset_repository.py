from __future__ import annotations

import pytest

from infra.preset_repository import (
    _PRESETS,
    PRESET_IDS,
    get_all_presets,
    get_preset,
)
from models.enums import ActionType, MouseButton
from models.scheme import Scheme

# ═══════════════════════════════════════════════════════════════════
# 08.1 — PRESET_IDS 唯一性
# ═══════════════════════════════════════════════════════════════════


class TestPresetIds:
    """测试预设 ID 常量的定义与唯一性。"""

    def test_preset_ids_unique(self) -> None:
        """4 个预设 ID 各不相同。"""
        values = list(PRESET_IDS.values())
        assert len(values) == len(set(values)), f"存在重复 ID: {values}"

    def test_preset_ids_count_is_four(self) -> None:
        """PRESET_IDS 恰好包含 4 个条目。"""
        assert len(PRESET_IDS) == 4

    def test_preset_ids_keys_match_design(self) -> None:
        """所有设计定义的 key 均存在。"""
        assert set(PRESET_IDS.keys()) == {"zha_yu", "xi_shuai", "gather", "clicker"}


# ═══════════════════════════════════════════════════════════════════
# 08.2 — preset_zha_yu（炸鱼）结构验证
# ═══════════════════════════════════════════════════════════════════


class TestPresetZhaYu:
    """测试炸鱼预设方案的结构。"""

    @pytest.fixture
    def scheme(self) -> Scheme:
        return get_preset(PRESET_IDS["zha_yu"])  # type: ignore[return-value]

    def test_zha_yu_exists(self, scheme: Scheme) -> None:
        """get_preset 返回非 None。"""
        assert scheme is not None

    def test_zha_yu_name(self, scheme: Scheme) -> None:
        assert scheme.name == "炸鱼"

    def test_zha_yu_loop(self, scheme: Scheme) -> None:
        assert scheme.loop is True

    def test_zha_yu_is_preset(self, scheme: Scheme) -> None:
        assert scheme.is_preset is True

    def test_zha_yu_action_count(self, scheme: Scheme) -> None:
        assert len(scheme.actions) == 2

    def test_zha_yu_action_0_key_press_4(self, scheme: Scheme) -> None:
        a = scheme.actions[0]
        assert a.action_type == ActionType.KEY_PRESS
        assert a.key == "4"
        assert a.order == 0

    def test_zha_yu_action_1_wait_random(self, scheme: Scheme) -> None:
        a = scheme.actions[1]
        assert a.action_type == ActionType.WAIT
        assert a.wait_min == 22.0
        assert a.wait_max == 24.0
        assert a.order == 1

    def test_zha_yu_default_hotkeys(self, scheme: Scheme) -> None:
        assert scheme.start_hotkey == "F10"
        assert scheme.stop_hotkey == "F12"


# ═══════════════════════════════════════════════════════════════════
# 08.3 — preset_xi_shuai（蟋蟀）结构验证
# ═══════════════════════════════════════════════════════════════════


class TestPresetXiShuai:
    """测试蟋蟀预设方案的结构。"""

    @pytest.fixture
    def scheme(self) -> Scheme:
        return get_preset(PRESET_IDS["xi_shuai"])  # type: ignore[return-value]

    def test_xi_shuai_exists(self, scheme: Scheme) -> None:
        assert scheme is not None

    def test_xi_shuai_name(self, scheme: Scheme) -> None:
        assert scheme.name == "蟋蟀"

    def test_xi_shuai_loop(self, scheme: Scheme) -> None:
        assert scheme.loop is True

    def test_xi_shuai_is_preset(self, scheme: Scheme) -> None:
        assert scheme.is_preset is True

    def test_xi_shuai_action_count(self, scheme: Scheme) -> None:
        assert len(scheme.actions) == 6

    def test_xi_shuai_action_0_mouse_left(self, scheme: Scheme) -> None:
        a = scheme.actions[0]
        assert a.action_type == ActionType.MOUSE_CLICK
        assert a.mouse_button == MouseButton.LEFT
        assert a.order == 0

    def test_xi_shuai_action_1_wait_100s(self, scheme: Scheme) -> None:
        a = scheme.actions[1]
        assert a.action_type == ActionType.WAIT
        assert a.wait_seconds == 100.0
        assert a.order == 1

    def test_xi_shuai_action_2_key_press_space(self, scheme: Scheme) -> None:
        a = scheme.actions[2]
        assert a.action_type == ActionType.KEY_PRESS
        assert a.key == "Space"
        assert a.order == 2

    def test_xi_shuai_action_3_wait_5s(self, scheme: Scheme) -> None:
        a = scheme.actions[3]
        assert a.action_type == ActionType.WAIT
        assert a.wait_seconds == 5.0
        assert a.order == 3

    def test_xi_shuai_action_4_key_press_f(self, scheme: Scheme) -> None:
        a = scheme.actions[4]
        assert a.action_type == ActionType.KEY_PRESS
        assert a.key == "F"
        assert a.order == 4

    def test_xi_shuai_action_5_wait_5s(self, scheme: Scheme) -> None:
        a = scheme.actions[5]
        assert a.action_type == ActionType.WAIT
        assert a.wait_seconds == 5.0
        assert a.order == 5

    def test_xi_shuai_all_orders_sequential(self, scheme: Scheme) -> None:
        """验证 6 个 action 的 order 从 0 到 5 严格递增。"""
        for i, action in enumerate(scheme.actions):
            assert action.order == i


# ═══════════════════════════════════════════════════════════════════
# 08.4 — preset_gather（自动采集）和 preset_clicker（连点器）
# ═══════════════════════════════════════════════════════════════════


class TestPresetGather:
    """测试自动采集预设方案的结构。"""

    @pytest.fixture
    def scheme(self) -> Scheme:
        return get_preset(PRESET_IDS["gather"])  # type: ignore[return-value]

    def test_gather_name(self, scheme: Scheme) -> None:
        assert scheme.name == "自动采集"

    def test_gather_loop(self, scheme: Scheme) -> None:
        assert scheme.loop is True

    def test_gather_is_preset(self, scheme: Scheme) -> None:
        assert scheme.is_preset is True

    def test_gather_action_count(self, scheme: Scheme) -> None:
        assert len(scheme.actions) == 2

    def test_gather_action_0_key_press_1(self, scheme: Scheme) -> None:
        a = scheme.actions[0]
        assert a.action_type == ActionType.KEY_PRESS
        assert a.key == "1"
        assert a.order == 0

    def test_gather_action_1_wait_random(self, scheme: Scheme) -> None:
        a = scheme.actions[1]
        assert a.action_type == ActionType.WAIT
        assert a.wait_min == 10.0
        assert a.wait_max == 12.0
        assert a.order == 1


class TestPresetClicker:
    """测试连点器预设方案的结构。"""

    @pytest.fixture
    def scheme(self) -> Scheme:
        return get_preset(PRESET_IDS["clicker"])  # type: ignore[return-value]

    def test_clicker_name(self, scheme: Scheme) -> None:
        assert scheme.name == "连点器"

    def test_clicker_loop(self, scheme: Scheme) -> None:
        assert scheme.loop is True

    def test_clicker_is_preset(self, scheme: Scheme) -> None:
        assert scheme.is_preset is True

    def test_clicker_action_count(self, scheme: Scheme) -> None:
        assert len(scheme.actions) == 2

    def test_clicker_action_0_key_press_f(self, scheme: Scheme) -> None:
        a = scheme.actions[0]
        assert a.action_type == ActionType.KEY_PRESS
        assert a.key == "F"
        assert a.order == 0

    def test_clicker_action_1_wait_015s(self, scheme: Scheme) -> None:
        a = scheme.actions[1]
        assert a.action_type == ActionType.WAIT
        assert a.wait_seconds == 0.15
        assert a.order == 1


# ═══════════════════════════════════════════════════════════════════
# 08.5 — get_all_presets() 和 get_preset() API
# ═══════════════════════════════════════════════════════════════════


class TestGetAllPresets:
    """测试公共 API 函数。"""

    def test_get_all_presets_returns_four(self) -> None:
        presets = get_all_presets()
        assert len(presets) == 4

    def test_get_all_presets_all_unique_ids(self) -> None:
        presets = get_all_presets()
        ids = [p.id for p in presets]
        assert len(ids) == len(set(ids))

    def test_get_all_presets_all_are_presets(self) -> None:
        presets = get_all_presets()
        for p in presets:
            assert p.is_preset is True, f"{p.id} 的 is_preset 应为 True"

    def test_get_all_presets_all_have_valid_names(self) -> None:
        presets = get_all_presets()
        for p in presets:
            assert p.name, f"{p.id} 的 name 不应为空"

    def test_get_preset_by_valid_ids(self) -> None:
        """get_preset 对全部 4 个有效 ID 均返回非 None。"""
        for pid in PRESET_IDS.values():
            result = get_preset(pid)
            assert result is not None, f"get_preset({pid!r}) 不应返回 None"
            assert result.id == pid

    def test_get_preset_by_invalid_id(self) -> None:
        """get_preset 对不存在的 ID 返回 None。"""
        assert get_preset("nonexistent_id") is None

    def test_get_preset_by_empty_string(self) -> None:
        """get_preset 对空字符串返回 None。"""
        assert get_preset("") is None

    def test_get_preset_by_partial_match(self) -> None:
        """get_preset 对部分匹配的 ID 返回 None（精确匹配）。"""
        assert get_preset("preset_zha") is None

    def test_get_all_presets_preserve_order(self) -> None:
        """get_all_presets 返回顺序固定：炸鱼、蟋蟀、自动采集、连点器。"""
        presets = get_all_presets()
        expected_ids = [
            PRESET_IDS["zha_yu"],
            PRESET_IDS["xi_shuai"],
            PRESET_IDS["gather"],
            PRESET_IDS["clicker"],
        ]
        actual_ids = [p.id for p in presets]
        assert actual_ids == expected_ids

    def test_get_all_presets_returns_new_list(self) -> None:
        """get_all_presets 每次返回新列表，调用方可安全修改。"""
        a = get_all_presets()
        b = get_all_presets()
        assert a is not b
        assert a == b

    def test_module_level_presets_match_api(self) -> None:
        """模块级 _PRESETS 与公开 API 返回一致。"""
        assert len(_PRESETS) == 4
        api_presets = get_all_presets()
        assert [p.id for p in _PRESETS] == [p.id for p in api_presets]


# ═══════════════════════════════════════════════════════════════════
# 跨方案一致性检查
# ═══════════════════════════════════════════════════════════════════


class TestCrossPresetConsistency:
    """测试所有预设方案之间的交叉一致性。"""

    def test_all_presets_have_default_f10_f12(self) -> None:
        """所有预设方案均使用默认的 F10 启动、F12 停止热键。"""
        for p in get_all_presets():
            assert p.start_hotkey == "F10", f"{p.id} start_hotkey"
            assert p.stop_hotkey == "F12", f"{p.id} stop_hotkey"

    def test_all_presets_loop_true(self) -> None:
        """所有预设方案均为循环模式。"""
        for p in get_all_presets():
            assert p.loop is True, f"{p.id} 的 loop 应为 True"

    def test_all_presets_have_description(self) -> None:
        """所有预设方案均有非空描述。"""
        for p in get_all_presets():
            assert p.description, f"{p.id} 的 description 不应为空"

    def test_no_two_presets_share_same_name(self) -> None:
        """任意两个预设方案名称不同。"""
        presets = get_all_presets()
        names = [p.name for p in presets]
        assert len(names) == len(set(names)), f"存在重名: {names}"

    def test_closed_under_to_dict_from_dict(self) -> None:
        """所有预设方案均可通过 to_dict/from_dict 往返序列化。"""
        for original in get_all_presets():
            restored = Scheme.from_dict(original.to_dict())
            assert restored == original, f"{original.id} 往返序列化失败"
            assert restored.is_preset is True
