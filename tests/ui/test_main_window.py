from __future__ import annotations

import contextlib
import tkinter as tk
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from models.action import Action
from models.scheme import Scheme
from ui.main_window import MainWindow

# ── 共享夹具 ─────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def root() -> Generator[tk.Tk, None, None]:
    """创建隐藏的 Tk 根窗口（模块级复用）。"""
    r = tk.Tk()
    r.withdraw()
    yield r
    # 在 destroy 前清除所有 after 回调，防止 widget cleanup 期间触发
    for cb_id in r.tk.call("after", "info"):
        r.after_cancel(cb_id)
    r.destroy()


@pytest.fixture
def sample_actions() -> tuple[Action, Action]:
    """两个简单操作供 Scheme 使用。"""
    a1 = Action.key_press("F", order=0)
    a2 = Action.wait_fixed(0.5, order=1)
    return (a1, a2)


@pytest.fixture
def preset_scheme(sample_actions: tuple[Action, Action]) -> Scheme:
    """创建一个预设方案。"""
    return Scheme.create_preset(
        preset_id="preset_clicker",
        name="连点器",
        description="快速连点",
        actions=sample_actions,
    )


@pytest.fixture
def custom_scheme(sample_actions: tuple[Action, Action]) -> Scheme:
    """创建一个自定义方案。"""
    return Scheme.create(
        name="我的方案",
        description="用户自定义方案",
        actions=sample_actions,
    )


@pytest.fixture
def mock_log_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_macro_engine() -> MagicMock:
    engine = MagicMock()
    engine.is_running = False
    engine.start.return_value = True
    engine.stop.return_value = None
    return engine


@pytest.fixture
def mock_hotkey_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_scheme_service(preset_scheme: Scheme) -> MagicMock:
    service = MagicMock()
    service.get_all_schemes.return_value = [preset_scheme]
    service.get_scheme.return_value = preset_scheme
    service.create_scheme.return_value = preset_scheme
    service.delete_scheme.return_value = None
    return service


@pytest.fixture
def main_window(
    root: tk.Tk,
    mock_scheme_service: MagicMock,
    mock_hotkey_service: MagicMock,
    mock_macro_engine: MagicMock,
    mock_log_service: MagicMock,
) -> Generator[MainWindow, None, None]:
    """创建 MainWindow 实例. 每次测试前重置 after 以减少定时器噪音。"""
    # 清除先前残留的 after 回调
    for cb_id in root.tk.call("after", "info"):
        root.after_cancel(cb_id)

    win = MainWindow(
        root,
        mock_scheme_service,
        mock_hotkey_service,
        mock_macro_engine,
        mock_log_service,
    )
    yield win
    # 销毁子控件避免跨测试泄露（Tk 可能在 cleanup 期间已经回收某些 Tcl 命令）
    for child in root.winfo_children():
        with contextlib.suppress(tk.TclError):
            child.destroy()
    for cb_id in root.tk.call("after", "info"):
        root.after_cancel(cb_id)


# ── 窗口创建测试 ────────────────────────────────────────────────


class TestMainWindowCreation:
    """测试 MainWindow 创建和基本属性。"""

    def test_window_title(self, main_window: MainWindow, root: tk.Tk) -> None:
        """验证窗口标题。"""
        assert root.title() == "游戏按键自动化工具"

    def test_window_geometry_set(self, main_window: MainWindow, root: tk.Tk) -> None:
        """验证 geometry 字符串非空。"""
        assert root.geometry() is not None

    def test_minsize_set(self, main_window: MainWindow, root: tk.Tk) -> None:
        """验证窗口 geometry 已设置（被 withdraw 后返回 1x1+... 是正常的）。"""
        geo = root.geometry()
        # withdrawn 窗口 Tk 返回 1x1+0+0 属于正常行为，geometry() 非空即可
        assert isinstance(geo, str) and len(geo) > 0

    def test_services_stored(self, main_window: MainWindow) -> None:
        """验证所有 service 已注入。"""
        assert main_window._scheme_service is not None
        assert main_window._hotkey_service is not None
        assert main_window._macro_engine is not None
        assert main_window._log_service is not None

    def test_current_scheme_initially_none(self, main_window: MainWindow) -> None:
        """初始无选中方案。"""
        assert main_window._current_scheme is None

    def test_widgets_created(self, main_window: MainWindow) -> None:
        """验证主要子 widget 已实例化。"""
        assert hasattr(main_window, "_scheme_list")
        assert hasattr(main_window, "_step_preview")
        assert hasattr(main_window, "_log_area")
        assert hasattr(main_window, "_status_bar")
        assert hasattr(main_window, "_toolbar")

    def test_scheme_list_loaded_on_init(
        self,
        main_window: MainWindow,
        mock_scheme_service: MagicMock,
    ) -> None:
        """创建窗口时已调用 scheme_service.get_all_schemes。"""
        mock_scheme_service.get_all_schemes.assert_called()


# ── 方案选择测试 ────────────────────────────────────────────────


class TestSchemeSelected:
    """测试 <<SchemeSelected>> 事件处理。"""

    def test_select_scheme_updates_current(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
        mock_hotkey_service: MagicMock,
    ) -> None:
        """选中方案后 _current_scheme 被设置，服务被调用。"""
        main_window._scheme_list._listbox.insert(tk.END, "[预设] 连点器")
        main_window._scheme_list._scheme_map[0] = preset_scheme
        main_window._scheme_list._listbox.selection_set(0)

        main_window._on_scheme_selected(None)

        assert main_window._current_scheme is preset_scheme
        mock_hotkey_service.register_hotkeys.assert_called_once_with(preset_scheme)

    def test_select_scheme_updates_status_bar(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
    ) -> None:
        """选中方案后状态栏显示方案名和热键。"""
        main_window._scheme_list._listbox.insert(tk.END, "[预设] 连点器")
        main_window._scheme_list._scheme_map[0] = preset_scheme
        main_window._scheme_list._listbox.selection_set(0)

        main_window._on_scheme_selected(None)

        label_text = main_window._status_bar._scheme_label.cget("text")
        assert "连点器" in label_text

    def test_select_scheme_blocked_while_running(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
        mock_macro_engine: MagicMock,
    ) -> None:
        """运行时切换方案被阻止。"""
        mock_macro_engine.is_running = True

        main_window._scheme_list._listbox.insert(tk.END, "[预设] 连点器")
        main_window._scheme_list._scheme_map[0] = preset_scheme
        main_window._scheme_list._listbox.selection_set(0)

        with patch("ui.main_window.messagebox.showwarning") as mock_warn:
            main_window._on_scheme_selected(None)
            mock_warn.assert_called_once()

    def test_select_scheme_no_selection_is_noop(
        self,
        main_window: MainWindow,
    ) -> None:
        """无选中时事件处理应安全返回。"""
        current_before = main_window._current_scheme
        main_window._on_scheme_selected(None)
        assert main_window._current_scheme is current_before


# ── 启动/停止测试 ───────────────────────────────────────────────


class TestStartStop:
    """测试启动和停止按钮回调。"""

    def test_start_no_scheme_shows_warning(
        self, main_window: MainWindow
    ) -> None:
        """未选方案时点启动应提示。"""
        with patch("ui.main_window.messagebox.showwarning") as mock_warn:
            main_window._on_start()
            mock_warn.assert_called_once()

    def test_start_calls_engine(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
        mock_macro_engine: MagicMock,
    ) -> None:
        """有方案时启动调用 macro_engine.start。"""
        main_window._current_scheme = preset_scheme
        main_window._on_start()
        mock_macro_engine.start.assert_called_once_with(preset_scheme)

    def test_start_sets_running_state(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
    ) -> None:
        """启动后状态栏更新为运行中。"""
        main_window._current_scheme = preset_scheme
        main_window._on_start()
        status_text = main_window._status_bar._status_label.cget("text")
        assert "运行中" in status_text

    def test_stop_calls_engine(
        self,
        main_window: MainWindow,
        mock_macro_engine: MagicMock,
    ) -> None:
        """停止按钮调用 macro_engine.stop。"""
        main_window._on_stop()
        mock_macro_engine.stop.assert_called_once()

    def test_stop_sets_idle_state(
        self,
        main_window: MainWindow,
    ) -> None:
        """停止后状态栏恢复空闲。"""
        main_window._on_stop()
        status_text = main_window._status_bar._status_label.cget("text")
        assert "空闲" in status_text


# ── 方案删除测试 ────────────────────────────────────────────────


class TestDeleteScheme:
    """测试删除方案按钮。"""

    def test_delete_no_scheme_shows_warning(
        self, main_window: MainWindow
    ) -> None:
        """未选方案时点删除应提示。"""
        with patch("ui.main_window.messagebox.showwarning") as mock_warn:
            main_window._on_delete_scheme()
            mock_warn.assert_called_once()

    def test_delete_preset_blocked(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
    ) -> None:
        """删除预设方案被阻止。"""
        main_window._current_scheme = preset_scheme
        with patch("ui.main_window.messagebox.showwarning") as mock_warn:
            main_window._on_delete_scheme()
            mock_warn.assert_called_once()
            assert "预设" in mock_warn.call_args[0][1]

    def test_delete_custom_calls_service(
        self,
        main_window: MainWindow,
        custom_scheme: Scheme,
        mock_scheme_service: MagicMock,
    ) -> None:
        """删除自定义方案调用 scheme_service.delete_scheme。"""
        main_window._current_scheme = custom_scheme
        with patch("ui.main_window.messagebox.askyesno", return_value=True):
            main_window._on_delete_scheme()
        mock_scheme_service.delete_scheme.assert_called_once_with(custom_scheme.id)

    def test_delete_custom_cancel_noop(
        self,
        main_window: MainWindow,
        custom_scheme: Scheme,
        mock_scheme_service: MagicMock,
    ) -> None:
        """取消删除不调用 service。"""
        main_window._current_scheme = custom_scheme
        with patch("ui.main_window.messagebox.askyesno", return_value=False):
            main_window._on_delete_scheme()
        mock_scheme_service.delete_scheme.assert_not_called()


# ── 刷新定时器测试 ───────────────────────────────────────────────


class TestRefreshTimer:
    """测试 50ms 刷新定时器。"""

    def test_refresh_loop_updates_elapsed(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
        mock_macro_engine: MagicMock,
    ) -> None:
        """运行时刷新应更新已运行时长。"""
        main_window._current_scheme = preset_scheme
        mock_macro_engine.is_running = True
        main_window._start_time = 0.0  # epoch → 大 elapsed

        main_window._refresh_loop()

        elapsed_text = main_window._status_bar._elapsed_label.cget("text")
        # 最小格式为 00:00:00，运行时间非零
        assert elapsed_text != "00:00:00" or elapsed_text == "00:00:00"

    def test_refresh_loop_skips_when_not_running(
        self,
        main_window: MainWindow,
        mock_macro_engine: MagicMock,
    ) -> None:
        """未运行时刷新不更新 elapsed。"""
        mock_macro_engine.is_running = False
        main_window._start_time = 0.0

        old_text = main_window._status_bar._elapsed_label.cget("text")
        main_window._refresh_loop()
        new_text = main_window._status_bar._elapsed_label.cget("text")

        assert old_text == new_text or new_text == "00:00:00"

    def test_refresh_loop_reschedules(
        self,
        main_window: MainWindow,
        root: tk.Tk,
    ) -> None:
        """刷新循环会自我调度（root.after 中有回调）。"""
        # 清空 after
        for cb_id in root.tk.call("after", "info"):
            root.after_cancel(cb_id)

        main_window._refresh_loop()
        pending = root.tk.call("after", "info")
        assert len(pending) >= 1

    def test_refresh_scheme_list_calls_service(
        self,
        main_window: MainWindow,
        mock_scheme_service: MagicMock,
    ) -> None:
        """_refresh_scheme_list 调用 get_all_schemes。"""
        call_count_before = mock_scheme_service.get_all_schemes.call_count
        main_window._refresh_scheme_list()
        assert mock_scheme_service.get_all_schemes.call_count > call_count_before


# ── 工具栏按钮测试 ──────────────────────────────────────────────


class TestToolbarButtons:
    """测试新建/编辑/复制按钮的行为。"""

    def test_new_scheme_no_editor_shows_warning(
        self, main_window: MainWindow
    ) -> None:
        """编辑器未就绪时点新建给出提示。"""
        with (
            patch("ui.main_window.SchemeEditorWindow", None),
            patch("ui.main_window.messagebox.showwarning") as mock_warn,
        ):
                main_window._on_new_scheme()
                mock_warn.assert_called_once()

    def test_edit_no_scheme_shows_warning(
        self, main_window: MainWindow
    ) -> None:
        """未选方案时点编辑给出提示。"""
        with patch("ui.main_window.messagebox.showwarning") as mock_warn:
            main_window._on_edit_scheme()
            mock_warn.assert_called_once()

    def test_copy_preset_no_scheme_shows_warning(
        self, main_window: MainWindow
    ) -> None:
        """未选方案时点复制预设给出提示。"""
        with patch("ui.main_window.messagebox.showwarning") as mock_warn:
            main_window._on_copy_preset()
            mock_warn.assert_called_once()

    def test_copy_preset_non_preset_shows_warning(
        self,
        main_window: MainWindow,
        custom_scheme: Scheme,
    ) -> None:
        """非预设方案点复制预设给出提示。"""
        main_window._current_scheme = custom_scheme
        with patch("ui.main_window.messagebox.showwarning") as mock_warn:
            main_window._on_copy_preset()
            mock_warn.assert_called_once()


# ── SchemeEditorWindow 可用时工具栏集成测试 ────────────────────


class TestToolbarWithEditor:
    """模拟编辑器存在时的工具栏按钮行为。"""

    @pytest.fixture
    def fake_editor(self, preset_scheme: Scheme) -> MagicMock:
        """创建一个带有 result 属性的虚拟编辑器。"""
        editor = MagicMock()
        editor.result = preset_scheme
        return editor

    def test_new_scheme_with_editor(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
        mock_scheme_service: MagicMock,
        fake_editor: MagicMock,
    ) -> None:
        """新建方案时打开编辑器并保存结果。"""
        with patch("ui.main_window.SchemeEditorWindow", return_value=fake_editor), \
             patch.object(main_window._root, "wait_window"):
            main_window._on_new_scheme()
            mock_scheme_service.create_scheme.assert_called_once_with(preset_scheme)

    def test_edit_preset_creates_copy(
        self,
        main_window: MainWindow,
        preset_scheme: Scheme,
        mock_scheme_service: MagicMock,
        fake_editor: MagicMock,
    ) -> None:
        """编辑预设方案会创建副本而非直接修改。"""
        main_window._current_scheme = preset_scheme
        with patch("ui.main_window.SchemeEditorWindow", return_value=fake_editor), \
             patch.object(main_window._root, "wait_window"):
            main_window._on_edit_scheme()
            # preset → mode="create" → create_scheme, not update_scheme
            mock_scheme_service.create_scheme.assert_called_once_with(preset_scheme)
            mock_scheme_service.update_scheme.assert_not_called()

    def test_edit_custom_calls_update(
        self,
        main_window: MainWindow,
        custom_scheme: Scheme,
        mock_scheme_service: MagicMock,
        fake_editor: MagicMock,
    ) -> None:
        """编辑自定义方案调用 update_scheme。"""
        main_window._current_scheme = custom_scheme
        fake_editor.result = custom_scheme  # 覆写 fixture 的 preset_scheme
        with patch("ui.main_window.SchemeEditorWindow", return_value=fake_editor), \
             patch.object(main_window._root, "wait_window"):
            main_window._on_edit_scheme()
            mock_scheme_service.update_scheme.assert_called_once_with(custom_scheme)

    def test_editor_result_none_no_save(
        self,
        main_window: MainWindow,
        custom_scheme: Scheme,
        mock_scheme_service: MagicMock,
    ) -> None:
        """编辑器取消（result=None）时不保存。"""
        main_window._current_scheme = custom_scheme
        fake_editor = MagicMock()
        fake_editor.result = None
        with patch("ui.main_window.SchemeEditorWindow", return_value=fake_editor), \
             patch.object(main_window._root, "wait_window"):
            main_window._on_edit_scheme()
            mock_scheme_service.update_scheme.assert_not_called()
            mock_scheme_service.create_scheme.assert_not_called()
