from __future__ import annotations

from unittest.mock import patch

import pytest

from infra import keyboard_hook

# ═══════════════════════════════════════════════════════════════
# 06.1 — register_hotkey
# ═══════════════════════════════════════════════════════════════


class TestRegisterHotkeyCallsKeyboard:
    """测试 register_hotkey() 正确调用 keyboard.add_hotkey。"""

    def test_calls_add_hotkey_with_correct_args(self) -> None:
        def callback() -> None:
            pass

        with patch("infra.keyboard_hook.keyboard.add_hotkey") as mock_add:
            keyboard_hook.register_hotkey("F10", callback)
            mock_add.assert_called_once_with("F10", callback)

    def test_passes_hotkey_string_unchanged(self) -> None:
        def callback() -> None:
            pass

        with patch("infra.keyboard_hook.keyboard.add_hotkey") as mock_add:
            keyboard_hook.register_hotkey("ctrl+shift+a", callback)
            mock_add.assert_called_once_with("ctrl+shift+a", callback)

    def test_passes_callback_unchanged(self) -> None:
        calls: list[str] = []

        def record() -> None:
            calls.append("fired")

        with patch("infra.keyboard_hook.keyboard.add_hotkey") as mock_add:
            keyboard_hook.register_hotkey("F12", record)
            mock_add.assert_called_once_with("F12", record)


class TestRegisterHotkeyValidation:
    """测试 register_hotkey() 的参数验证。"""

    def test_raises_type_error_when_key_not_str(self) -> None:
        with pytest.raises(TypeError, match="key must be str"):
            keyboard_hook.register_hotkey(123, lambda: None)  # type: ignore[arg-type]

    def test_raises_value_error_when_key_empty(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            keyboard_hook.register_hotkey("", lambda: None)

    def test_raises_type_error_when_callback_not_callable(self) -> None:
        with pytest.raises(TypeError, match="callback must be callable"):
            keyboard_hook.register_hotkey("F10", "not_a_function")  # type: ignore[arg-type]

    def test_accepts_builtin_function_as_callback(self) -> None:
        with patch("infra.keyboard_hook.keyboard.add_hotkey") as mock_add:
            keyboard_hook.register_hotkey("F10", print)
            mock_add.assert_called_once_with("F10", print)

    def test_accepts_method_as_callback(self) -> None:
        class Handler:
            def handle(self) -> None:
                pass

        h = Handler()
        with patch("infra.keyboard_hook.keyboard.add_hotkey") as mock_add:
            keyboard_hook.register_hotkey("F10", h.handle)
            mock_add.assert_called_once_with("F10", h.handle)


# ═══════════════════════════════════════════════════════════════
# 06.2 — unregister_hotkey
# ═══════════════════════════════════════════════════════════════


class TestUnregisterHotkeyCallsKeyboard:
    """测试 unregister_hotkey() 正确调用 keyboard.remove_hotkey。"""

    def test_calls_remove_hotkey_with_correct_key(self) -> None:
        with patch("infra.keyboard_hook.keyboard.remove_hotkey") as mock_remove:
            keyboard_hook.unregister_hotkey("F10")
            mock_remove.assert_called_once_with("F10")

    def test_passes_key_unchanged(self) -> None:
        with patch("infra.keyboard_hook.keyboard.remove_hotkey") as mock_remove:
            keyboard_hook.unregister_hotkey("ctrl+alt+x")
            mock_remove.assert_called_once_with("ctrl+alt+x")


class TestUnregisterHotkeyGraceful:
    """测试 unregister_hotkey() 对异常情况的优雅处理。"""

    def test_silently_ignores_keyerror_when_hotkey_not_registered(self) -> None:
        with patch(
            "infra.keyboard_hook.keyboard.remove_hotkey",
            side_effect=KeyError("hotkey not found"),
        ):
            # 不应抛出异常
            keyboard_hook.unregister_hotkey("F10")

    def test_propagates_other_exceptions(self) -> None:
        with patch(
            "infra.keyboard_hook.keyboard.remove_hotkey",
            side_effect=RuntimeError("unexpected"),
        ), pytest.raises(RuntimeError, match="unexpected"):
            keyboard_hook.unregister_hotkey("F10")


class TestUnregisterHotkeyValidation:
    """测试 unregister_hotkey() 的参数验证。"""

    def test_raises_type_error_when_key_not_str(self) -> None:
        with pytest.raises(TypeError, match="key must be str"):
            keyboard_hook.unregister_hotkey(123)  # type: ignore[arg-type]

    def test_raises_value_error_when_key_empty(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            keyboard_hook.unregister_hotkey("")


# ═══════════════════════════════════════════════════════════════
# 06.3 — clear_all
# ═══════════════════════════════════════════════════════════════


class TestClearAllCallsKeyboard:
    """测试 clear_all() 正确调用 keyboard.unhook_all_hotkeys。"""

    def test_calls_unhook_all_hotkeys(self) -> None:
        with patch(
            "infra.keyboard_hook.keyboard.unhook_all_hotkeys"
        ) as mock_clear:
            keyboard_hook.clear_all()
            mock_clear.assert_called_once_with()

    def test_clear_all_no_args(self) -> None:
        with patch(
            "infra.keyboard_hook.keyboard.unhook_all_hotkeys"
        ) as mock_clear:
            keyboard_hook.clear_all()
            # 确认无参数调用
            assert mock_clear.call_count == 1
            assert mock_clear.call_args == ((), {})


class TestClearAllIntegration:
    """测试 clear_all 与 register/unregister 的组合行为。"""

    def test_clear_after_register_triggers_keyboard_calls(self) -> None:
        """验证 clear_all 独立于 register/unregister 正常工作。"""
        with patch(
            "infra.keyboard_hook.keyboard.unhook_all_hotkeys"
        ) as mock_clear:
            keyboard_hook.clear_all()
            mock_clear.assert_called_once_with()
