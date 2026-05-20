from __future__ import annotations

import tkinter as tk

import pytest

from models.action import Action
from models.scheme import Scheme
from ui.widgets.scheme_list import SchemeListWidget

# ── 辅助夹具 ────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def root() -> tk.Tk:  # type: ignore[misc]
    """创建 Tk 根窗口用于测试（模块级，只初始化一次）。"""
    r = tk.Tk()
    r.withdraw()  # 不显示窗口
    yield r
    r.destroy()


@pytest.fixture
def sample_actions() -> tuple[Action, Action]:
    """创建两个简单操作供 Scheme 使用。"""
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
def mixed_schemes(
    preset_scheme: Scheme, custom_scheme: Scheme, sample_actions: tuple[Action, Action]
) -> list[Scheme]:
    """返回混合的预设和自定义方案列表：4 个预设 + 2 个自定义。"""
    presets = [
        Scheme.create_preset("p1", f"预设{i}", f"描述{i}", sample_actions)
        for i in range(1, 5)
    ]
    customs = [
        Scheme.create(name=f"自定义{j}", description=f"自定义描述{j}", actions=sample_actions)
        for j in range(1, 3)
    ]
    return presets + customs


# ── 测试 ────────────────────────────────────────────────────────


class TestSchemeListWidgetCreation:
    """测试 Widget 创建和基本布局。"""

    def test_widget_creation(self, root: tk.Tk) -> None:
        """验证 SchemeListWidget 可正常创建且子控件存在。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()

        root.update()

        # 标题应包含 "方案列表"
        children = widget.winfo_children()
        assert len(children) >= 2  # 标题 + list_frame

        widget.destroy()

    def test_widget_has_listbox(self, root: tk.Tk) -> None:
        """验证 Listbox 控件存在且为单选模式。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        assert hasattr(widget, "_listbox")
        assert widget._listbox.cget("selectmode") == "browse"

        widget.destroy()


class TestRefresh:
    """测试 refresh() 数据填充。"""

    def test_refresh_populates_list_items(self, root: tk.Tk, mixed_schemes: list[Scheme]) -> None:
        """传入 4 preset + 2 custom，验证 Listbox 包含 6 项。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh(mixed_schemes)
        root.update()

        assert widget._listbox.size() == 6
        widget.destroy()

    def test_refresh_shows_preset_prefix(self, root: tk.Tk, preset_scheme: Scheme) -> None:
        """预设方案应显示 [预设] 前缀。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh([preset_scheme])
        root.update()

        first = widget._listbox.get(0)
        assert first.startswith("[预设]")
        widget.destroy()

    def test_refresh_shows_custom_prefix(self, root: tk.Tk, custom_scheme: Scheme) -> None:
        """自定义方案应显示 [自定义] 前缀。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh([custom_scheme])
        root.update()

        first = widget._listbox.get(0)
        assert first.startswith("[自定义]")
        widget.destroy()

    def test_refresh_clears_previous_items(
        self, root: tk.Tk, preset_scheme: Scheme, custom_scheme: Scheme
    ) -> None:
        """第二次 refresh 应清空旧条目。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh([preset_scheme, custom_scheme])
        root.update()
        assert widget._listbox.size() == 2

        widget.refresh([custom_scheme])
        root.update()
        assert widget._listbox.size() == 1

        widget.destroy()


class TestGetSelected:
    """测试 get_selected() 方法。"""

    def test_get_selected_returns_none_when_nothing_selected(
        self, root: tk.Tk, mixed_schemes: list[Scheme]
    ) -> None:
        """无选择时应返回 None。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh(mixed_schemes)
        root.update()

        assert widget.get_selected() is None
        widget.destroy()

    def test_get_selected_returns_correct_scheme(
        self, root: tk.Tk, mixed_schemes: list[Scheme]
    ) -> None:
        """选择某个索引后应返回正确的 Scheme。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh(mixed_schemes)
        root.update()

        # 选中第 3 项（索引 2）
        widget._listbox.selection_set(2)
        root.update()

        result = widget.get_selected()
        assert result is not None
        assert result is mixed_schemes[2]
        widget.destroy()

    def test_get_selected_after_deselect(
        self, root: tk.Tk, mixed_schemes: list[Scheme]
    ) -> None:
        """取消选择后应返回 None。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh(mixed_schemes)
        root.update()

        widget._listbox.selection_set(1)
        root.update()
        assert widget.get_selected() is not None

        widget._listbox.selection_clear(0, tk.END)
        root.update()
        assert widget.get_selected() is None

        widget.destroy()


class TestSchemeSelectedEvent:
    """测试 <<SchemeSelected>> 虚拟事件。"""

    def test_scheme_selected_event_fired_on_click(
        self, root: tk.Tk, mixed_schemes: list[Scheme]
    ) -> None:
        """点击选项时 <<SchemeSelected>> 事件应被触发。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh(mixed_schemes)
        root.update()

        events_received: list[object] = []

        def on_scheme_selected(event: object) -> None:
            events_received.append(event)

        widget.bind("<<SchemeSelected>>", on_scheme_selected)

        # 模拟选取：直接调用 _on_select 模拟 Tk 事件分派
        widget._listbox.selection_set(0)
        widget._on_select(None)

        assert len(events_received) == 1
        widget.destroy()

    def test_scheme_selected_event_not_fired_on_creation(
        self, root: tk.Tk, mixed_schemes: list[Scheme]
    ) -> None:
        """Widget 创建和 refresh 时不应触发事件（仅在用户选择时）。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        events_received: list[object] = []

        def on_scheme_selected(event: object) -> None:
            events_received.append(event)

        widget.bind("<<SchemeSelected>>", on_scheme_selected)

        widget.refresh(mixed_schemes)
        root.update()

        # refresh 本身不应触发选择事件（Tk 在编程式插入时不会自动触发 <<ListboxSelect>>）
        assert len(events_received) == 0
        widget.destroy()


class TestSchemeMapIntegrity:
    """测试 _scheme_map 在 refresh 后的完整性。"""

    def test_scheme_map_has_correct_size(
        self, root: tk.Tk, mixed_schemes: list[Scheme]
    ) -> None:
        """_scheme_map 条目数应与列表中的方案数一致。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh(mixed_schemes)
        root.update()

        assert len(widget._scheme_map) == len(mixed_schemes)
        for i, scheme in enumerate(mixed_schemes):
            assert widget._scheme_map[i] is scheme

        widget.destroy()

    def test_scheme_map_cleared_on_refresh(
        self, root: tk.Tk, preset_scheme: Scheme, custom_scheme: Scheme
    ) -> None:
        """第二次 refresh 后 _scheme_map 索引应重新映射。"""
        widget = SchemeListWidget(root)  # type: ignore[arg-type]
        widget.pack()
        root.update()

        widget.refresh([preset_scheme])
        root.update()
        assert len(widget._scheme_map) == 1

        widget.refresh([custom_scheme, preset_scheme])
        root.update()
        assert len(widget._scheme_map) == 2
        assert widget._scheme_map[0] is custom_scheme
        assert widget._scheme_map[1] is preset_scheme

        widget.destroy()
