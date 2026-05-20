from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from models.scheme import Scheme


class StepPreviewWidget(tk.Frame):
    """只读操作步骤预览组件。

    显示当前方案的步骤编号列表（1-based），每条为 action.__str__() 的可读描述。
    带有垂直滚动条，行高固定为 10 行。
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self._build_ui()

    # ── 布局 ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """创建标题标签 + Listbox + 滚动条的布局。"""
        title = tk.Label(self, text="操作步骤预览", anchor="w")
        title.pack(fill="x", pady=(0, 4))

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self._listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=10,
            state="disabled",
            exportselection=False,
        )
        self._listbox.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self._listbox.yview)

    # ── 公开方法 ───────────────────────────────────────────────

    def set_scheme(self, scheme: Scheme) -> None:
        """加载方案并显示其操作步骤。

        Args:
            scheme: 要预览的方案对象
        """
        self._enable_editing()
        self._listbox.delete(0, "end")
        for i, action in enumerate(scheme.actions):
            self._listbox.insert("end", f"{i + 1}. {action}")
        self._disable_editing()

    def clear(self) -> None:
        """清空列表中的所有步骤。"""
        self._enable_editing()
        self._listbox.delete(0, "end")
        self._disable_editing()

    # ── 内部辅助 ───────────────────────────────────────────────

    def _enable_editing(self) -> None:
        self._listbox.configure(state="normal")

    def _disable_editing(self) -> None:
        self._listbox.configure(state="disabled")
