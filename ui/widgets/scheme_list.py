from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from models.scheme import Scheme


class SchemeListWidget(tk.Frame):
    """方案列表控件。

    显示所有方案（区分预设/自定义），支持单选，选中时触发
    <<SchemeSelected>> 虚拟事件，供父窗口监听。
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self._scheme_map: dict[int, Scheme] = {}
        self._build_ui()

    # ── 界面构建 ────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """创建标题标签、Listbox 和滚动条。"""
        title = ttk.Label(self, text="方案列表")
        title.pack(fill=tk.X, padx=2, pady=(2, 0))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self._listbox = tk.Listbox(
            list_frame, selectmode="browse", exportselection=False
        )
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self._listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.configure(yscrollcommand=scrollbar.set)

        self._listbox.bind("<<ListboxSelect>>", self._on_select)

    # ── 数据填充 ────────────────────────────────────────────────

    def refresh(self, schemes: list[Scheme]) -> None:
        """用方案列表填充 Listbox。

        清空现有条目后按顺序插入，每项显示 "[预设] Name"
        或 "[自定义] Name"，并建立索引到 Scheme 的映射。

        Args:
            schemes: 要显示的 Scheme 对象列表。
        """
        self._listbox.delete(0, tk.END)
        self._scheme_map.clear()

        for i, scheme in enumerate(schemes):
            prefix = "[预设]" if scheme.is_preset else "[自定义]"
            label = f"{prefix} {scheme.name}"
            self._listbox.insert(tk.END, label)
            self._scheme_map[i] = scheme

    # ── 查询 ────────────────────────────────────────────────────

    def get_selected(self) -> Scheme | None:
        """返回当前选中的 Scheme，没有选中时返回 None。"""
        selected = self._listbox.curselection()  # type: ignore[no-untyped-call]
        if not selected:
            return None
        return self._scheme_map.get(selected[0])

    # ── 事件处理 ────────────────────────────────────────────────

    def _on_select(self, event: object) -> None:
        """Listbox 选择变化时发出 <<SchemeSelected>> 虚拟事件。

        父窗口可绑定 <<SchemeSelected>> 来响应方案切换。

        Args:
            event: Tkinter 的 <<ListboxSelect>> 事件对象。
        """
        self.event_generate("<<SchemeSelected>>", when="now")
