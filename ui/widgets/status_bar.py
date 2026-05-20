from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

from models.scheme import Scheme


class StatusBarWidget(tk.Frame):
    """状态栏组件：显示当前方案信息、运行状态、运行时长和启停按钮。

    单行布局（7 列 grid）：
    [方案名] [热键] [状态指示] [已运行时间] [spacer] [启动] [停止]
    """

    def __init__(
        self,
        master: tk.Widget,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_start: Callable[[], None] | None = on_start
        self._on_stop: Callable[[], None] | None = on_stop
        self._running: bool = False

        # 列权重：col 4 作为弹性 spacer，将按钮推到右侧
        for i in range(7):
            self.columnconfigure(i, weight=0)
        self.columnconfigure(4, weight=1)

        self._scheme_label = tk.Label(self, text="方案: --", anchor="w")
        self._scheme_label.grid(row=0, column=0, padx=(5, 4), sticky="w")

        self._hotkey_label = tk.Label(self, text="热键: -- / --")
        self._hotkey_label.grid(row=0, column=1, padx=4, sticky="w")

        self._status_label = tk.Label(self, text="○ 空闲", fg="gray")
        self._status_label.grid(row=0, column=2, padx=4, sticky="w")

        self._elapsed_label = tk.Label(self, text="00:00:00")
        self._elapsed_label.grid(row=0, column=3, padx=4, sticky="w")

        self._start_btn = tk.Button(
            self, text="启动", command=self._handle_start
        )
        self._start_btn.grid(row=0, column=5, padx=2, sticky="e")

        self._stop_btn = tk.Button(
            self, text="停止", command=self._handle_stop, state="disabled"
        )
        self._stop_btn.grid(row=0, column=6, padx=(2, 5), sticky="e")

    # ── 公共 API ──────────────────────────────────────────────

    def set_scheme(self, scheme: Scheme) -> None:
        """更新方案信息：名称和热键。"""
        self._scheme_label.configure(text=f"方案: {scheme.name}")
        hotkey_text = f"热键: {scheme.start_hotkey} / {scheme.stop_hotkey}"
        self._hotkey_label.configure(text=hotkey_text)

    def set_running(self, running: bool) -> None:
        """更新运行状态指示器并切换按钮启用/禁用。"""
        self._running = running
        self._refresh_status()
        self._refresh_buttons()

    def update_elapsed(self, seconds: float) -> None:
        """更新已运行时间显示（格式化为 HH:MM:SS）。"""
        self._elapsed_label.configure(text=self._format_elapsed(seconds))

    def set_start_command(self, command: Callable[[], None]) -> None:
        """设置启动按钮的回调函数。"""
        self._on_start = command
        self._start_btn.configure(command=command)

    def set_stop_command(self, command: Callable[[], None]) -> None:
        """设置停止按钮的回调函数。"""
        self._on_stop = command
        self._stop_btn.configure(command=command)

    # ── 内部方法 ──────────────────────────────────────────────

    def _handle_start(self) -> None:
        if self._on_start is not None:
            self._on_start()

    def _handle_stop(self) -> None:
        if self._on_stop is not None:
            self._on_stop()

    def _refresh_status(self) -> None:
        """根据 _running 刷新状态指示灯文本和颜色。"""
        if self._running:
            self._status_label.configure(text="● 运行中", fg="green")
        else:
            self._status_label.configure(text="○ 空闲", fg="gray")

    def _refresh_buttons(self) -> None:
        """根据 _running 刷新按钮启用/禁用状态。"""
        if self._running:
            self._start_btn.configure(state="disabled")
            self._stop_btn.configure(state="normal")
        else:
            self._start_btn.configure(state="normal")
            self._stop_btn.configure(state="disabled")

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        """将秒数格式化为 HH:MM:SS 字符串。"""
        total = max(0, int(seconds))
        hours = total // 3600
        minutes = (total % 3600) // 60
        secs = total % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    # ── 兼容方法 ──────────────────────────────────────────────

    def update_state(
        self,
        scheme_name: str | None = None,
        hotkeys: tuple[str, str] | None = None,
        is_running: bool | None = None,
        elapsed_seconds: float | None = None,
    ) -> None:
        """批量部分更新状态。仅更新提供了非 None 值的标签。

        Args:
            scheme_name: 方案名称（None 表示不更新）
            hotkeys: (start_hotkey, stop_hotkey) 元组（None 表示不更新）
            is_running: 是否运行中（None 表示不更新）
            elapsed_seconds: 已运行秒数（None 表示不更新）
        """
        if scheme_name is not None:
            self._scheme_label.configure(text=f"方案: {scheme_name}")
        if hotkeys is not None:
            self._hotkey_label.configure(
                text=f"热键: {hotkeys[0]} / {hotkeys[1]}"
            )
        if is_running is not None:
            self._running = is_running
            self._refresh_status()
            self._refresh_buttons()
        if elapsed_seconds is not None:
            self.update_elapsed(elapsed_seconds)
