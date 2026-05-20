from __future__ import annotations

import tkinter as tk
from collections.abc import Generator

import pytest

from models.action import Action
from models.enums import ActionType
from models.scheme import Scheme
from ui.widgets.step_preview import StepPreviewWidget

# ── fixtures ───────────────────────────────────────────────────


@pytest.fixture(scope="session")
def root() -> Generator[tk.Tk, None, None]:
    """创建隐藏的 Tk 根窗口（整个测试会话复用）。"""
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def widget(root: tk.Tk) -> Generator[StepPreviewWidget, None, None]:
    """创建 StepPreviewWidget 实例，测试后销毁。"""
    w = StepPreviewWidget(root)  # type: ignore[arg-type]
    w.pack()
    root.update()
    yield w
    w.destroy()


# ── helper ─────────────────────────────────────────────────────


def _make_scheme(actions: tuple[Action, ...]) -> Scheme:
    """用给定 actions 构造一个测试用 Scheme。"""
    return Scheme.create(
        name="测试方案",
        description="用于测试",
        actions=actions,
    )


def _dummy_action(order: int, key: str = "Space") -> Action:
    """创建一个简单的 KEY_PRESS action。"""
    return Action(
        action_type=ActionType.KEY_PRESS,
        order=order,
        key=key,
        duration=0.1,
    )


# ── tests ──────────────────────────────────────────────────────


def test_widget_creation(widget: StepPreviewWidget) -> None:
    """验证组件创建后 Listbox 为空且处于禁用状态。"""
    lb = widget._listbox
    assert lb.size() == 0
    assert str(lb.cget("state")) == "disabled"


def test_set_scheme_populates(widget: StepPreviewWidget) -> None:
    """传入含 5 个 action 的 Scheme，验证 Listbox 内容正确。"""
    actions = tuple(_dummy_action(i, key) for i, key in enumerate(
        ["Space", "F", "1", "E", "Q"], start=1,
    ))
    scheme = _make_scheme(actions)

    widget.set_scheme(scheme)

    lb = widget._listbox
    assert lb.size() == 5
    expected = [
        "1. 按键 Space (0.1s)",
        "2. 按键 F (0.1s)",
        "3. 按键 1 (0.1s)",
        "4. 按键 E (0.1s)",
        "5. 按键 Q (0.1s)",
    ]
    for i, text in enumerate(expected):
        assert lb.get(i) == text
    # 设置后应恢复为禁用
    assert str(lb.cget("state")) == "disabled"


def test_set_scheme_replaces_previous(widget: StepPreviewWidget) -> None:
    """连续调用 set_scheme 应替换而非追加。"""
    first = _make_scheme((_dummy_action(1, "A"), _dummy_action(2, "B")))
    second = _make_scheme((_dummy_action(1, "X"),))

    widget.set_scheme(first)
    widget.set_scheme(second)

    lb = widget._listbox
    assert lb.size() == 1
    assert lb.get(0) == "1. 按键 X (0.1s)"


def test_clear(widget: StepPreviewWidget) -> None:
    """set scheme 后 clear，验证 Listbox size 为 0。"""
    actions = (_dummy_action(1, "F"), _dummy_action(2, "G"))
    scheme = _make_scheme(actions)

    widget.set_scheme(scheme)
    assert widget._listbox.size() == 2

    widget.clear()
    assert widget._listbox.size() == 0
    assert str(widget._listbox.cget("state")) == "disabled"


def test_clear_on_empty_listbox(widget: StepPreviewWidget) -> None:
    """对空 Listbox 调用 clear 不应报错。"""
    assert widget._listbox.size() == 0
    widget.clear()
    assert widget._listbox.size() == 0
