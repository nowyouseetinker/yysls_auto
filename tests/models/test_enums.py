from __future__ import annotations

from enum import Enum

from models.enums import ActionType, MouseButton


class TestActionType:
    """ActionType 枚举的测试。"""

    def test_is_str_enum(self) -> None:
        assert issubclass(ActionType, str)
        assert issubclass(ActionType, Enum)

    def test_member_count(self) -> None:
        members = list(ActionType)
        assert len(members) == 3

    def test_member_values(self) -> None:
        assert ActionType.KEY_PRESS.value == "key_press"
        assert ActionType.MOUSE_CLICK.value == "mouse_click"
        assert ActionType.WAIT.value == "wait"

    def test_values_are_lowercase_snake_case(self) -> None:
        for member in ActionType:
            assert member.value == member.value.lower()
            assert " " not in member.value
            assert "_" in member.value or member.value.isalpha()

    def test_all_members_covered(self) -> None:
        expected = {"key_press", "mouse_click", "wait"}
        actual = {member.value for member in ActionType}
        assert actual == expected

    def test_member_names(self) -> None:
        expected_names = {"KEY_PRESS", "MOUSE_CLICK", "WAIT"}
        actual_names = {member.name for member in ActionType}
        assert actual_names == expected_names

    def test_str_usage(self) -> None:
        """str 子类的枚举可直接用于字符串比较。"""
        val: str = ActionType.MOUSE_CLICK
        assert isinstance(val, str)


class TestMouseButton:
    """MouseButton 枚举的测试。"""

    def test_is_str_enum(self) -> None:
        assert issubclass(MouseButton, str)
        assert issubclass(MouseButton, Enum)

    def test_member_count(self) -> None:
        members = list(MouseButton)
        assert len(members) == 2

    def test_member_values(self) -> None:
        assert MouseButton.LEFT.value == "left"
        assert MouseButton.RIGHT.value == "right"

    def test_values_are_lowercase(self) -> None:
        for member in MouseButton:
            assert member.value == member.value.lower()

    def test_all_members_covered(self) -> None:
        expected = {"left", "right"}
        actual = {member.value for member in MouseButton}
        assert actual == expected

    def test_member_names(self) -> None:
        expected_names = {"LEFT", "RIGHT"}
        actual_names = {member.name for member in MouseButton}
        assert actual_names == expected_names


class TestEnumIntegration:
    """两个枚举之间的集成测试。"""

    def test_action_type_references_mouse_button_correctly(self) -> None:
        """确保 MOUSE_CLICK 与 MouseButton 枚举可配合使用。"""
        action = ActionType.MOUSE_CLICK
        button = MouseButton.LEFT
        assert action == "mouse_click"
        assert button == "left"

    def test_enums_are_separate(self) -> None:
        """确认两个枚举是独立的。"""
        assert ActionType.__members__ != MouseButton.__members__
        action_values = {m.value for m in ActionType}
        mouse_values = {m.value for m in MouseButton}
        assert not action_values & mouse_values
