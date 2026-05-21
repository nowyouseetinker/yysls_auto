from __future__ import annotations

import time
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from models.scheme import Scheme
from services.hotkey_service import HotkeyService
from services.log_service import LogService
from services.macro_engine import MacroEngine
from services.scheme_service import SchemeService
from ui.theme import (
    ACCENT_BLUE,
    BG_BASE,
    BORDER,
    BTN_DEFAULT,
    BTN_PRIMARY,
    FONT_FAMILY,
    TEXT_PRIMARY,
    label_font,
)
from ui.widgets.log_area import LogAreaWidget
from ui.widgets.scheme_list import SchemeListWidget
from ui.widgets.status_bar import StatusBarWidget
from ui.widgets.step_preview import StepPreviewWidget

try:
    from ui.scheme_editor import SchemeEditorWindow
except ImportError:
    SchemeEditorWindow = None  # type: ignore[assignment,misc]

_REFRESH_INTERVAL_MS: int = 50

# Shared toolbar button font (created after root exists)
_TOOL_FONT: ctk.CTkFont | None = None

def _tool_font() -> ctk.CTkFont:
    global _TOOL_FONT
    if _TOOL_FONT is None:
        _TOOL_FONT = ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")
    return _TOOL_FONT


class MainWindow:
    """游戏按键自动化工具主窗口 — CTk 现代化版本。"""

    def __init__(
        self,
        root: ctk.CTk,
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
        root.geometry("880x640")
        root.minsize(680, 480)

        self._setup_ui()
        self._bind_events()
        self._refresh_scheme_list()
        self._start_refresh_loop()

    # ── UI 布局 ──────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = self._root
        root.configure(fg_color=BG_BASE)

        # Main container
        main = ctk.CTkFrame(root, fg_color="transparent")
        main.pack(fill=ctk.BOTH, expand=True, padx=8, pady=8)

        main.columnconfigure(0, weight=0, minsize=170)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=0)  # title row
        main.rowconfigure(1, weight=1)  # right side content
        main.rowconfigure(2, weight=0)  # status bar
        main.rowconfigure(3, weight=0)  # toolbar

        # ── Left: Scheme list ────────────────────────────────────
        left_panel = ctk.CTkFrame(main, fg_color="transparent")
        left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 6))
        left_panel.rowconfigure(1, weight=1)

        ctk.CTkLabel(
            left_panel, text="方案列表", font=label_font(),
            text_color=TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self._scheme_list = SchemeListWidget(left_panel)
        self._scheme_list.grid(row=1, column=0, sticky="nsew")

        # ── Right side: PanedWindow (preview ↑ | log ↓) ─────────
        self._right_pane = tk.PanedWindow(
            main,
            orient=tk.VERTICAL,
            bg="#FFFFFF",
            sashwidth=6,
            sashrelief="flat",
            sashpad=0,
            handlesize=10,
        )
        self._right_pane.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(6, 0))

        # Step preview (upper pane)
        self._step_preview = StepPreviewWidget(self._right_pane)
        self._right_pane.add(self._step_preview, stretch="always")

        # Log area (lower pane)
        self._log_area = LogAreaWidget(self._right_pane, self._log_service, height=6)
        self._right_pane.add(self._log_area, stretch="always")

        # Set initial 6:4 ratio via pane sizes
        self._right_pane.after(100, self._set_pane_ratio)

        # ── Status bar ───────────────────────────────────────────
        self._status_bar = StatusBarWidget(
            main, on_start=self._on_start, on_stop=self._on_stop
        )
        self._status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 4))

        # ── Toolbar ──────────────────────────────────────────────
        self._toolbar = self._build_toolbar(main)
        self._toolbar.grid(row=3, column=0, columnspan=2, sticky="ew")

    def _set_pane_ratio(self) -> None:
        """Set PanedWindow sash to 6:4 ratio after geometry is computed."""
        try:
            height = self._right_pane.winfo_height()
            if height > 20:
                self._right_pane.sash_place(0, 0, int(height * 0.6))
        except Exception:
            pass  # not yet mapped

    def _build_toolbar(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        """Compact flat toolbar with strong hover feedback."""
        frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=8,
                             border_width=1, border_color=BORDER)
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill=ctk.X, padx=4, pady=3)

        btn_font = _tool_font()

        for text, cmd in [
            ("新建方案", self._on_new_scheme),
            ("编辑方案", self._on_edit_scheme),
            ("删除方案", self._on_delete_scheme),
            ("复制预设", self._on_copy_preset),
        ]:
            ctk.CTkButton(inner, text=text, command=cmd,
                          font=btn_font, **BTN_DEFAULT,
                          ).pack(side=ctk.LEFT, padx=2)

        # Separator
        sep = ctk.CTkFrame(inner, width=1, height=18, fg_color=BORDER)
        sep.pack(side=ctk.LEFT, padx=4)

        ctk.CTkButton(inner, text="导出方案", command=self._on_export_scheme,
                       font=btn_font, **BTN_DEFAULT,
                       ).pack(side=ctk.LEFT, padx=2)
        ctk.CTkButton(inner, text="导入方案", command=self._on_import_scheme,
                       font=btn_font, **BTN_DEFAULT,
                       ).pack(side=ctk.LEFT, padx=2)
        return frame

    # ── Event bindings ──────────────────────────────────────────

    def _bind_events(self) -> None:
        self._root.bind("<<SchemeSelected>>", self._on_scheme_selected)

    # ── Refresh loop ────────────────────────────────────────────

    def _start_refresh_loop(self) -> None:
        self._root.after(_REFRESH_INTERVAL_MS, self._refresh_loop)

    def _refresh_loop(self) -> None:
        if self._macro_engine.is_running and self._start_time > 0:
            elapsed = time.monotonic() - self._start_time
            self._status_bar.update_state(elapsed_seconds=elapsed)
        self._root.after(_REFRESH_INTERVAL_MS, self._refresh_loop)

    def _refresh_scheme_list(self) -> None:
        schemes = self._scheme_service.get_all_schemes()
        self._scheme_list.refresh(schemes)

    # ── Event handlers ──────────────────────────────────────────

    def _on_scheme_selected(self, event: object) -> None:
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
        if self._current_scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案")
            return
        self._macro_engine.start(self._current_scheme)
        self._start_time = time.monotonic()
        self._status_bar.update_state(is_running=True)

    def _on_stop(self) -> None:
        self._macro_engine.stop()
        self._status_bar.update_state(is_running=False)

    # ── Scheme CRUD ─────────────────────────────────────────────

    def _on_new_scheme(self) -> None:
        if SchemeEditorWindow is None:
            messagebox.showwarning("提示", "方案编辑器暂不可用"); return
        editor = SchemeEditorWindow(self._root, mode="create")
        self._root.wait_window(editor)
        if editor.result is not None:
            self._scheme_service.create_scheme(editor.result)
            self._refresh_scheme_list()

    def _on_edit_scheme(self) -> None:
        if SchemeEditorWindow is None:
            messagebox.showwarning("提示", "方案编辑器暂不可用"); return
        scheme = self._current_scheme
        if scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案"); return
        mode = "create" if scheme.is_preset else "edit"
        editor = SchemeEditorWindow(self._root, mode=mode, scheme=scheme)
        self._root.wait_window(editor)
        if editor.result is not None:
            if scheme.is_preset:
                self._scheme_service.create_scheme(editor.result)
            else:
                self._scheme_service.update_scheme(editor.result)
            self._refresh_scheme_list()

    def _on_delete_scheme(self) -> None:
        scheme = self._current_scheme
        if scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案"); return
        if scheme.is_preset:
            messagebox.showwarning("提示", "预设方案不可删除"); return
        if not messagebox.askyesno("确认删除", f"确定要删除方案「{scheme.name}」吗？"):
            return
        self._scheme_service.delete_scheme(scheme.id)
        self._current_scheme = None
        self._step_preview.clear()
        self._status_bar.update_state(scheme_name="--", hotkeys=("--", "--"), is_running=False)
        self._refresh_scheme_list()

    def _on_copy_preset(self) -> None:
        if SchemeEditorWindow is None:
            messagebox.showwarning("提示", "方案编辑器暂不可用"); return
        scheme = self._current_scheme
        if scheme is None or not scheme.is_preset:
            messagebox.showwarning("提示", "请选择一个预设方案"); return
        editor = SchemeEditorWindow(self._root, mode="create", scheme=scheme)
        self._root.wait_window(editor)
        if editor.result is not None:
            self._scheme_service.create_scheme(editor.result)
            self._refresh_scheme_list()

    # ── Export / Import ─────────────────────────────────────────

    def _on_export_scheme(self) -> None:
        scheme = self._current_scheme
        if scheme is None:
            messagebox.showwarning("提示", "请先选择一个方案"); return
        try:
            export_str = scheme.to_export_string()
            self._root.clipboard_clear()
            self._root.clipboard_append(export_str)
            messagebox.showinfo("导出成功",
                f"方案「{scheme.name}」已复制到剪贴板。")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def _on_import_scheme(self) -> None:
        dialog = ctk.CTkToplevel(self._root)
        dialog.title("导入方案")
        dialog.transient(self._root)
        dialog.grab_set()
        dialog.resizable(False, False)

        frame = ctk.CTkFrame(dialog, fg_color="#FFFFFF", corner_radius=8)
        frame.pack(fill=ctk.BOTH, expand=True, padx=12, pady=12)

        ctk.CTkLabel(frame, text="请粘贴导出方案时复制的字符串：",
                      font=label_font(), text_color=TEXT_PRIMARY,
                      ).pack(anchor=ctk.W)

        text = ctk.CTkTextbox(frame, height=5, width=56, corner_radius=6,
                              border_width=1, border_color=BORDER,
                              font=ctk.CTkFont(family="Consolas", size=12))
        text.pack(fill=ctk.BOTH, expand=True, pady=(8, 12))

        def do_import() -> None:
            raw = text.get("1.0", "end").strip()
            if not raw:
                messagebox.showwarning("提示", "请先粘贴内容", parent=dialog); return
            try:
                scheme = Scheme.from_export_string(raw)
            except ValueError as exc:
                messagebox.showerror("导入失败", str(exc), parent=dialog); return
            self._scheme_service.create_scheme(scheme)
            self._refresh_scheme_list()
            dialog.destroy()
            messagebox.showinfo("导入成功", f"方案「{scheme.name}」已导入")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill=ctk.X)
        ctk.CTkButton(btn_row, text="导入", command=do_import,
                       **BTN_PRIMARY).pack(side=ctk.RIGHT, padx=(4, 0))
        ctk.CTkButton(btn_row, text="取消", command=dialog.destroy,
                       **BTN_DEFAULT).pack(side=ctk.RIGHT)
