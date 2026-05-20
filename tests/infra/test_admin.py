from __future__ import annotations

from unittest.mock import patch

from infra.admin import is_admin


def test_is_admin_returns_true_when_api_says_true() -> None:
    """is_admin returns True when the Windows API reports admin."""
    with patch("infra.admin.ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
        assert is_admin() is True


def test_is_admin_returns_false_when_api_says_false() -> None:
    """is_admin returns False when the Windows API reports non-admin."""
    with patch("infra.admin.ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
        assert is_admin() is False


def test_is_admin_returns_false_on_error() -> None:
    """is_admin returns False when the API call raises an exception."""
    with patch(
        "infra.admin.ctypes.windll.shell32.IsUserAnAdmin",
        side_effect=OSError("simulated failure"),
    ):
        assert is_admin() is False


def test_is_admin_returns_bool_type() -> None:
    """The return value is always a bool, not an int."""
    with patch("infra.admin.ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
        result = is_admin()
        assert isinstance(result, bool)

    with patch("infra.admin.ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
        result = is_admin()
        assert isinstance(result, bool)


def test_elevate_does_nothing_when_already_admin() -> None:
    """elevate() returns immediately without calling ShellExecuteW when already admin."""
    with (
        patch("infra.admin.is_admin", return_value=True),
        patch("infra.admin.ctypes.windll.shell32.ShellExecuteW") as mock_shell,
        patch("infra.admin.sys.exit") as mock_exit,
    ):
        from infra.admin import elevate

        elevate()
        mock_shell.assert_not_called()
        mock_exit.assert_not_called()
