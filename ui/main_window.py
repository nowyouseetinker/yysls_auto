from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox, ttk

from models.scheme import Scheme
from services.hotkey_service import HotkeyService
from services.log_service import LogService
from services.macro_engine import MacroEngine
from services.scheme_service import SchemeService
from ui.widgets.log_area import LogAreaWidget
from ui.widgets.scheme_list import SchemeListWidget
from ui.widgets.status_bar import StatusBarWidget
from ui.widgets.step_preview import StepPreviewWidget

try:
    from ui.scheme_editor import SchemeEditorWindow
except ImportError:
    SchemeEditorWindow = None  # type: ignore[assignment,misc]

_REFRESH_INTERVAL_MS: int = 50


class MainWindow:
    """游戏按键自动化工具主窗口。

    组合方案列表、步骤预览、日志区和状态栏等 widget，
    通过 50ms 定时器刷新 UI，协调各服务与 widget 之间的交互。
    """

    def __init__(
        self,
        root: tk.Tk,
        scheme_service: SchemeService,
        hotkey_service: HotkeyService,
        macro_engine: MacroEngine,
        log_service: LogService,
    ) -> None:
        self._root = root
        self._scheme_service = scheme_service
        self._hotkey_service = hotkey_service
        self._macro_engine = macro_engine
        self._log_service = log_service

        self._current_scheme: Scheme | None = None
        self._start_time: float = 0.0

        root.title("游戏按键自动化工具")
        root.geometry("800x600")
        root.minsize(600, 400)

        self._setup_ui()
        self._bind_events()
        self._refresh_scheme_list()
        self._start_refresh_loop()

    # ── UI 布局 ──────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """构建完整布局：左列方案列表 | 右列步骤预览+日志 | 状态栏 | 工具栏。"""
        root = self._root
        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.rowconfigure(2, weight=0)
        root.rowconfigure(3, weight=0)

        self._scheme_list = SchemeListWidget(root)  # type: ignore[arg-type]
        self._scheme_list.grid(
            row=0, column=0, rowspan=2, sticky="nsew", padx=4, pady=4
        )

        self._step_preview = StepPreviewWidget(root)  # type: ignore[arg-type]
        self._step_preview.grid(
            row=0, column=1, sticky="nsew", padx=(0, 4), pady=(4, 2)
        )

        self._log_area = LogAreaWidget(root, self._log_service, height=8)  # type: ignore[arg-type]
        self._log_area.grid(
            row=1, column=1, sticky="nsew", padx=(0, 4), pady=(2, 4)
        )

        self._status_bar = StatusBarWidget(
            root, on_start=self._on_start, on_stop=self._on_stop  # type: ignore[arg-type]
        )
        self._status_bar.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 2)
        )

        self._toolbar = self._build_toolbar()
        self._toolbar.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4)
        )

    def _build_toolbar(self) -> ttk.Frame:
        """创建底部工具栏按钮。"""
        frame = ttk.Frame(self._root)
        ttk.Button(frame, text="新建方案", command=self._on_new_scheme).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(frame, text="编辑方案", command=self._on_edit_scheme).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(frame, text="删除方案", command=self._on_delete_scheme).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(frame, text="复制预设", command=self._on_copy_preset).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Separator(frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        ttk.Button(frame, text="导出方案", command=self._on_export_scheme).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(frame, text="导入方案", command=self._on_import_scheme).pack(
            side=tk.LEFT, padx=2
        )
        return frame

    # ── 事件绑定 ────────────────────────────────────────────────

    def _bind_events(self) -> None:
        """绑定虚拟事件到处理函数。"""
        self._root.bind("<<SchemeSelected>>", self._on_scheme_selected)

    # ── 刷新循环 ────────────────────────────────────────────────

    def _start_refresh_loop(self) -> None:
        """启动 50ms 刷新定时器。"""
        self._root.after(_REFRESH_INTERVAL_MS, self._refresh_loop)

    def _refresh_loop(self) -> None:
        """每 50ms 更新一次 UI 状态。"""
        if self._macro_engine.is_running and self._start_time > 0:
            elapsed = time.monotonic() - self._start_time
            self._status_bar.update_state(elapsed_seconds=elapsed)
        self._root.after(_REFRESH_INTERVAL_MS, self._refresh_loop)

    # ── 方案列表操作 ────────────────────────────────────────────

    def _refresh_scheme_list(self) -> None:
        """从 service 获取全部方案并刷新列表。"""
        schemes = self._scheme_service.get_all_schemes()
        self._scheme_list.refresh(schemes)

    # ── 事件处理 ────────────────────────────────────────────────

    def _on_scheme_selected(self, event: object) -> None:
        """处理方案选中：防止运行时切换，更新预览/状态栏/热键。"""
        if self._macro_engine.is_running:
            messagebox.showwarning("提示", "请先停止当前方案")
            return

        scheme = self._scheme_list.get_selected()
        if scheme is None:
            return

        self._current_scheme = scheme
        self._hotkey_service.register_hotkeys(scheme)
        self._step_preview.set_scheme(scheme)
        self._status_bar.update_state(
            scheme_name=scheme.name,
            hotkeys=(scheme.start_hotkey, scheme.stop_hotkey),
        )

    def _on_start(self) -> None:
        """启动按钮回调：执行当前方案。"""
        if self._current_scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案")
            return
        self._macro_engine.start(self._current_scheme)
        self._start_time = time.monotonic()
        self._status_bar.update_state(is_running=True)

    def _on_stop(self) -> None:
        """停止按钮回调：停止宏引擎。"""
        self._macro_engine.stop()
        self._status_bar.update_state(is_running=False)

    # ── 方案管理按钮 ────────────────────────────────────────────

    def _on_new_scheme(self) -> None:
        """打开新建方案编辑器并保存结果。"""
        if SchemeEditorWindow is None:
            messagebox.showwarning("提示", "方案编辑器暂不可用")
            return
        editor = SchemeEditorWindow(self._root, mode="create")  # type: ignore[arg-type]
        self._root.wait_window(editor)
        if editor.result is not None:
            self._scheme_service.create_scheme(editor.result)
            self._refresh_scheme_list()

    def _on_edit_scheme(self) -> None:
        """编辑当前选中方案。预设先复制，自定义直接编辑。"""
        if SchemeEditorWindow is None:
            messagebox.showwarning("提示", "方案编辑器暂不可用")
            return
        scheme = self._current_scheme
        if scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案")
            return
        if scheme.is_preset:
            editor = SchemeEditorWindow(self._root, mode="create", scheme=scheme)  # type: ignore[arg-type]
            self._root.wait_window(editor)
            if editor.result is not None:
                self._scheme_service.create_scheme(editor.result)
                self._refresh_scheme_list()
        else:
            editor = SchemeEditorWindow(self._root, mode="edit", scheme=scheme)  # type: ignore[arg-type]
            self._root.wait_window(editor)
            if editor.result is not None:
                self._scheme_service.update_scheme(editor.result)
                self._refresh_scheme_list()

    def _on_delete_scheme(self) -> None:
        """删除当前方案，预设方案禁止删除。"""
        scheme = self._current_scheme
        if scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案")
            return
        if scheme.is_preset:
            messagebox.showwarning("提示", "预设方案不可删除")
            return
        confirmed = messagebox.askyesno("确认删除", f"确定要删除方案「{scheme.name}」吗？")
        if not confirmed:
            return
        self._scheme_service.delete_scheme(scheme.id)
        self._current_scheme = None
        self._step_preview.clear()
        self._status_bar.update_state(
            scheme_name="--", hotkeys=("--", "--"), is_running=False
        )
        self._refresh_scheme_list()

    def _on_copy_preset(self) -> None:
        """复制当前预设方案为自定义方案。"""
        if SchemeEditorWindow is None:
            messagebox.showwarning("提示", "方案编辑器暂不可用")
            return
        scheme = self._current_scheme
        if scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案")
            return
        if not scheme.is_preset:
            messagebox.showwarning("提示", "仅预设方案可以复制")
            return
        editor = SchemeEditorWindow(self._root, mode="create", scheme=scheme)  # type: ignore[arg-type]
        self._root.wait_window(editor)
        if editor.result is not None:
            self._scheme_service.create_scheme(editor.result)
            self._refresh_scheme_list()

    # ── 导出 / 导入 ────────────────────────────────────────────

    def _on_export_scheme(self) -> None:
        """将当前方案编码为 base64 字符串并复制到剪贴板。"""
        scheme = self._current_scheme
        if scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案")
            return
        try:
            export_str = scheme.to_export_string()
            self._root.clipboard_clear()
            self._root.clipboard_append(export_str)
            messagebox.showinfo(
                "导出成功",
                f"方案「{scheme.name}」已复制到剪贴板。\n\n"
                f"在另一台电脑上点击「导入方案」粘贴即可。",
            )
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def _on_import_scheme(self) -> None:
        """打开导入对话框，粘贴导出字符串并创建方案。"""
        dialog = tk.Toplevel(self._root)
        dialog.title("导入方案")
        dialog.transient(self._root)
        dialog.grab_set()
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="请粘贴导出方案时复制的字符串：").pack(anchor=tk.W)

        text = tk.Text(frame, height=4, width=60, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, pady=(6, 10))
        text.focus_set()

        def do_import() -> None:
            raw = text.get("1.0", tk.END).strip()
            if not raw:
                messagebox.showwarning("提示", "请先粘贴内容", parent=dialog)
                return
            try:
                scheme = Scheme.from_export_string(raw)
            except ValueError as exc:
                messagebox.showerror("导入失败", str(exc), parent=dialog)
                return
            self._scheme_service.create_scheme(scheme)
            self._refresh_scheme_list()
            dialog.destroy()
            messagebox.showinfo("导入成功", f"方案「{scheme.name}」已导入")

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="导入", command=do_import).pack(
            side=tk.RIGHT, padx=(4, 0)
        )
        ttk.Button(btn_row, text="取消", command=dialog.destroy).pack(
            side=tk.RIGHT
        )

        # 居中
        dialog.update_idletasks()
        px = self._root.winfo_rootx() + 80
        py = self._root.winfo_rooty() + 80
        dialog.geometry(f"+{px}+{py}")
