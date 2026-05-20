from __future__ import annotations

import tkinter as tk

import pytest

from models.action import Action
from models.scheme import Scheme
from ui.widgets.status_bar import StatusBarWidget

# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture(scope="session")
def root() -> tk.Tk:  # type: ignore[misc]
    """创建并返回隐藏的 Tk 根窗口（会话级，不销毁以避免无法重建）。"""
    r = tk.Tk()
    r.withdraw()
    yield r
    # 注意：不调用 destroy()，因为 Tkinter 在销毁后无法重建 Tk 实例


@pytest.fixture
def widget(root: tk.Tk) -> StatusBarWidget:  # type: ignore[misc]
    """在根窗口中创建 StatusBarWidget。"""
    w = StatusBarWidget(root)  # type: ignore[arg-type]
    yield w
    w.destroy()


def _make_scheme(
    name: str = "测试方案",
    start_hotkey: str = "F10",
    stop_hotkey: str = "F12",
) -> Scheme:
    """工厂辅助：创建单个操作的 Scheme。"""
    actions: tuple[Action, ...] = (Action.key_press("Space", order=0),)
    return Scheme.create(
        name=name,
        description="测试用方案",
        actions=actions,
        start_hotkey=start_hotkey,
        stop_hotkey=stop_hotkey,
    )


# ── 16.1 — 控件创建 ──────────────────────────────────────────


class TestWidgetCreation:
    """测试 StatusBarWidget 的创建和初始状态。"""

    def test_creates_all_labels(self, widget: StatusBarWidget) -> None:
        children = widget.winfo_children()
        label_texts = {
            c.cget("text") for c in children if isinstance(c, tk.Label)
        }
        assert "方案: --" in label_texts
        assert "热键: -- / --" in label_texts
        assert "○ 空闲" in label_texts
        assert "00:00:00" in label_texts

    def test_creates_both_buttons(self, widget: StatusBarWidget) -> None:
        buttons = [
            c
            for c in widget.winfo_children()
            if isinstance(c, tk.Button)
        ]
        assert len(buttons) == 2
        button_texts = {b.cget("text") for b in buttons}
        assert "启动" in button_texts
        assert "停止" in button_texts

    def test_initial_status_is_idle(self, widget: StatusBarWidget) -> None:
        text = widget._status_label.cget("text")
        fg = widget._status_label.cget("fg")
        assert text == "○ 空闲"
        assert fg == "gray"

    def test_initial_elapsed_is_zero(self, widget: StatusBarWidget) -> None:
        assert widget._elapsed_label.cget("text") == "00:00:00"

    def test_initial_start_enabled_stop_disabled(
        self, widget: StatusBarWidget
    ) -> None:
        assert widget._start_btn.cget("state") == "normal"
        assert widget._stop_btn.cget("state") == "disabled"

    def test_is_frame_subclass(self) -> None:
        assert issubclass(StatusBarWidget, tk.Frame)


# ── 16.1 延伸 — set_scheme ───────────────────────────────────


class TestSetScheme:
    """测试 set_scheme() 更新方案信息标签。"""

    def test_updates_scheme_name(self, widget: StatusBarWidget) -> None:
        scheme = _make_scheme(name="炸鱼方案")
        widget.set_scheme(scheme)
        assert widget._scheme_label.cget("text") == "方案: 炸鱼方案"

    def test_updates_hotkey_display(self, widget: StatusBarWidget) -> None:
        scheme = _make_scheme(start_hotkey="F5", stop_hotkey="F8")
        widget.set_scheme(scheme)
        assert widget._hotkey_label.cget("text") == "热键: F5 / F8"

    def test_does_not_change_status(self, widget: StatusBarWidget) -> None:
        old_text = widget._status_label.cget("text")
        old_fg = widget._status_label.cget("fg")
        scheme = _make_scheme()
        widget.set_scheme(scheme)
        assert widget._status_label.cget("text") == old_text
        assert widget._status_label.cget("fg") == old_fg

    def test_does_not_change_elapsed(self, widget: StatusBarWidget) -> None:
        widget.update_elapsed(120.0)
        assert widget._elapsed_label.cget("text") == "00:02:00"
        scheme = _make_scheme()
        widget.set_scheme(scheme)
        # set_scheme 不应改动 elapsed
        assert widget._elapsed_label.cget("text") == "00:02:00"


# ── 16.2 / 16.4 — set_running 与按钮状态 ──────────────────────


class TestSetRunning:
    """测试 set_running() 切换运行状态和按钮状态。"""

    def test_running_true_shows_running_indicator(
        self, widget: StatusBarWidget
    ) -> None:
        widget.set_running(True)
        assert widget._status_label.cget("text") == "● 运行中"
        assert widget._status_label.cget("fg") == "green"

    def test_running_false_shows_idle_indicator(
        self, widget: StatusBarWidget
    ) -> None:
        widget.set_running(True)
        widget.set_running(False)
        assert widget._status_label.cget("text") == "○ 空闲"
        assert widget._status_label.cget("fg") == "gray"

    def test_running_disables_start_enables_stop(
        self, widget: StatusBarWidget
    ) -> None:
        widget.set_running(True)
        assert widget._start_btn.cget("state") == "disabled"
        assert widget._stop_btn.cget("state") == "normal"

    def test_stopped_enables_start_disables_stop(
        self, widget: StatusBarWidget
    ) -> None:
        widget.set_running(True)
        widget.set_running(False)
        assert widget._start_btn.cget("state") == "normal"
        assert widget._stop_btn.cget("state") == "disabled"


# ── 16.2 — update_elapsed ────────────────────────────────────


class TestUpdateElapsed:
    """测试 update_elapsed() 时间格式化显示。"""

    def test_displays_zero(self, widget: StatusBarWidget) -> None:
        widget.update_elapsed(0.0)
        assert widget._elapsed_label.cget("text") == "00:00:00"

    def test_displays_seconds(self, widget: StatusBarWidget) -> None:
        widget.update_elapsed(59.0)
        assert widget._elapsed_label.cget("text") == "00:00:59"

    def test_displays_minutes(self, widget: StatusBarWidget) -> None:
        widget.update_elapsed(120.0)
        assert widget._elapsed_label.cget("text") == "00:02:00"

    def test_displays_hours(self, widget: StatusBarWidget) -> None:
        widget.update_elapsed(3661.0)
        assert widget._elapsed_label.cget("text") == "01:01:01"

    def test_displays_max_typical(self, widget: StatusBarWidget) -> None:
        widget.update_elapsed(86399.0)
        assert widget._elapsed_label.cget("text") == "23:59:59"

    def test_negative_seconds_clamped_to_zero(
        self, widget: StatusBarWidget
    ) -> None:
        widget.update_elapsed(-5.0)
        assert widget._elapsed_label.cget("text") == "00:00:00"

    def test_float_truncated(self, widget: StatusBarWidget) -> None:
        widget.update_elapsed(65.9)
        assert widget._elapsed_label.cget("text") == "00:01:05"


# ── 16.3 — _format_elapsed 静态方法 ───────────────────────────


class TestFormatElapsed:
    """测试 _format_elapsed() 静态辅助方法。"""

    def test_zero_seconds(self) -> None:
        assert StatusBarWidget._format_elapsed(0.0) == "00:00:00"

    def test_one_hour_one_minute_one_second(self) -> None:
        assert StatusBarWidget._format_elapsed(3661.0) == "01:01:01"

    def test_almost_one_day(self) -> None:
        assert StatusBarWidget._format_elapsed(86399.0) == "23:59:59"

    def test_negative_seconds(self) -> None:
        assert StatusBarWidget._format_elapsed(-10.0) == "00:00:00"

    def test_large_value(self) -> None:
        result = StatusBarWidget._format_elapsed(100000.0)
        assert result == "27:46:40"


# ── 16.2 — update_state 部分更新 ──────────────────────────────


class TestUpdateState:
    """测试 update_state() 批量部分更新。"""

    def test_updates_only_scheme_name(self, widget: StatusBarWidget) -> None:
        before_status = widget._status_label.cget("text")
        before_elapsed = widget._elapsed_label.cget("text")
        widget.update_state(scheme_name="部分更新测试")
        assert widget._scheme_label.cget("text") == "方案: 部分更新测试"
        assert widget._status_label.cget("text") == before_status
        assert widget._elapsed_label.cget("text") == before_elapsed

    def test_updates_only_hotkeys(self, widget: StatusBarWidget) -> None:
        widget.update_state(hotkeys=("F1", "F12"))
        assert widget._hotkey_label.cget("text") == "热键: F1 / F12"

    def test_updates_only_running_status(
        self, widget: StatusBarWidget
    ) -> None:
        widget.update_state(is_running=True)
        assert widget._status_label.cget("text") == "● 运行中"
        assert widget._status_label.cget("fg") == "green"
        assert widget._start_btn.cget("state") == "disabled"
        assert widget._stop_btn.cget("state") == "normal"

    def test_updates_only_elapsed(self, widget: StatusBarWidget) -> None:
        widget.update_state(elapsed_seconds=3661.0)
        assert widget._elapsed_label.cget("text") == "01:01:01"

    def test_updates_all_fields(self, widget: StatusBarWidget) -> None:
        widget.update_state(
            scheme_name="全字段",
            hotkeys=("F5", "F8"),
            is_running=True,
            elapsed_seconds=120.0,
        )
        assert widget._scheme_label.cget("text") == "方案: 全字段"
        assert widget._hotkey_label.cget("text") == "热键: F5 / F8"
        assert widget._status_label.cget("text") == "● 运行中"
        assert widget._elapsed_label.cget("text") == "00:02:00"

    def test_none_params_do_nothing(self, widget: StatusBarWidget) -> None:
        """None 参数不应修改任何标签。"""
        widget.update_state(
            scheme_name="初始名称",
            hotkeys=("F1", "F2"),
            is_running=False,
            elapsed_seconds=0.0,
        )
        saved = (
            widget._scheme_label.cget("text"),
            widget._hotkey_label.cget("text"),
            widget._status_label.cget("text"),
            widget._elapsed_label.cget("text"),
        )
        widget.update_state()
        assert widget._scheme_label.cget("text") == saved[0]
        assert widget._hotkey_label.cget("text") == saved[1]
        assert widget._status_label.cget("text") == saved[2]
        assert widget._elapsed_label.cget("text") == saved[3]


# ── 16.1 延伸 — 按钮回调 ──────────────────────────────────────


class TestButtonCallbacks:
    """测试按钮点击回调机制。"""

    def test_start_button_calls_callback(self, root: tk.Tk) -> None:
        called: list[bool] = []

        def on_start() -> None:
            called.append(True)

        w = StatusBarWidget(root, on_start=on_start)  # type: ignore[arg-type]
        try:
            w._start_btn.invoke()
            assert called == [True]
        finally:
            w.destroy()

    def test_stop_button_calls_callback(self, root: tk.Tk) -> None:
        called: list[bool] = []

        def on_stop() -> None:
            called.append(True)

        w = StatusBarWidget(root, on_stop=on_stop)  # type: ignore[arg-type]
        # 停止按钮初始禁用，需先启用
        w.set_running(True)
        try:
            w._stop_btn.invoke()
            assert called == [True]
        finally:
            w.destroy()

    def test_set_start_command_updates_callback(
        self, root: tk.Tk
    ) -> None:
        called: list[str] = []
        w = StatusBarWidget(root)  # type: ignore[arg-type]
        try:
            w.set_start_command(lambda: called.append("new"))
            w._start_btn.invoke()
            assert called == ["new"]
        finally:
            w.destroy()

    def test_set_stop_command_updates_callback(
        self, root: tk.Tk
    ) -> None:
        called: list[str] = []
        w = StatusBarWidget(root)  # type: ignore[arg-type]
        w.set_running(True)
        try:
            w.set_stop_command(lambda: called.append("new"))
            w._stop_btn.invoke()
            assert called == ["new"]
        finally:
            w.destroy()

    def test_no_callback_does_not_raise(self, root: tk.Tk) -> None:
        """无回调时点击按钮不应抛出异常。"""
        w = StatusBarWidget(root)  # type: ignore[arg-type]
        try:
            w._start_btn.invoke()  # 无回调，不应异常
            w.set_running(True)
            w._stop_btn.invoke()  # 无回调，不应异常
        finally:
            w.destroy()

    def test_none_callback_does_not_raise(self, root: tk.Tk) -> None:
        """显式传入 None 时点击按钮不应抛出异常。"""
        w = StatusBarWidget(root, on_start=None, on_stop=None)  # type: ignore[arg-type]
        try:
            w._start_btn.invoke()
            w.set_running(True)
            w._stop_btn.invoke()
        finally:
            w.destroy()


# ── 按钮状态转换 ──────────────────────────────────────────────


class TestButtonStateTransitions:
    """测试运行状态转换时按钮启用/禁用的完整状态机。"""

    def test_initial_disabled_stop(self, widget: StatusBarWidget) -> None:
        assert widget._start_btn.cget("state") == "normal"
        assert widget._stop_btn.cget("state") == "disabled"

    def test_roundtrip_states(self, widget: StatusBarWidget) -> None:
        # 启动 → 停止 → 启动 → 停止
        widget.set_running(True)
        assert widget._start_btn.cget("state") == "disabled"
        assert widget._stop_btn.cget("state") == "normal"

        widget.set_running(False)
        assert widget._start_btn.cget("state") == "normal"
        assert widget._stop_btn.cget("state") == "disabled"

        widget.set_running(True)
        assert widget._start_btn.cget("state") == "disabled"
        assert widget._stop_btn.cget("state") == "normal"

        widget.set_running(False)
        assert widget._start_btn.cget("state") == "normal"
        assert widget._stop_btn.cget("state") == "disabled"

    def test_update_state_toggles_buttons(
        self, widget: StatusBarWidget
    ) -> None:
        widget.update_state(is_running=True)
        assert widget._start_btn.cget("state") == "disabled"
        assert widget._stop_btn.cget("state") == "normal"

        widget.update_state(is_running=False)
        assert widget._start_btn.cget("state") == "normal"
        assert widget._stop_btn.cget("state") == "disabled"
