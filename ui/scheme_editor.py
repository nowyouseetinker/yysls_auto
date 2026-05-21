from __future__ import annotations

import uuid
import customtkinter as ctk
from tkinter import messagebox

from models.action import Action
from models.enums import ActionType, MouseButton
from models.scheme import Scheme
from ui.theme import (
    ACCENT_BLUE,
    BG_CARD,
    BORDER,
    BTN_DANGER,
    BTN_DEFAULT,
    BTN_PRIMARY,
    FONT_FAMILY,
    TEXT_PRIMARY,
    label_font,
    small_font,
)


# ── Lazy dialog font helpers (created after root exists) ───────────

_DIALOG_FONT: ctk.CTkFont | None = None
_DIALOG_BOLD: ctk.CTkFont | None = None
_DIALOG_SMALL: ctk.CTkFont | None = None

def _df(size: int = 12, bold: bool = False) -> ctk.CTkFont:
    global _DIALOG_FONT, _DIALOG_BOLD, _DIALOG_SMALL
    w = "bold" if bold else "normal"
    if bold and _DIALOG_BOLD is None:
        _DIALOG_BOLD = ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")
    if not bold and size == 12 and _DIALOG_FONT is None:
        _DIALOG_FONT = ctk.CTkFont(family=FONT_FAMILY, size=12)
    if not bold and size == 11 and _DIALOG_SMALL is None:
        _DIALOG_SMALL = ctk.CTkFont(family=FONT_FAMILY, size=11)
    if bold:
        return _DIALOG_BOLD
    if size <= 11:
        return _DIALOG_SMALL
    return _DIALOG_FONT


# ── type-to-ui mapping ──────────────────────────────────────────────

def _action_to_ui_type(action: Action) -> str:
    if action.action_type == ActionType.KEY_PRESS:
        return "按键"
    if action.action_type == ActionType.MOUSE_CLICK:
        return "鼠标点击"
    if action.action_type == ActionType.WAIT:
        return "固定等待" if action.wait_seconds is not None else "随机等待"
    return "按键"


# ── Scheme editor dialog ────────────────────────────────────────────

class SchemeEditorWindow(ctk.CTkToplevel):
    """Modal dialog for creating or editing a Scheme."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        mode: str = "create",
        scheme: Scheme | None = None,
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self.result: Scheme | None = None

        if mode == "edit" and scheme is not None and scheme.is_preset:
            scheme = Scheme(
                id=uuid.uuid4().hex,
                name=scheme.name + " (副本)",
                description=scheme.description,
                actions=scheme.actions,
                loop=scheme.loop,
                start_hotkey=scheme.start_hotkey,
                stop_hotkey=scheme.stop_hotkey,
                is_preset=False,
            )

        self._initial_scheme = scheme
        self._actions: list[Action] = (
            list(scheme.actions) if scheme is not None else []
        )
        self._selected_action_idx: int | None = None
        self._item_widgets: list[dict] = []  # cached item widget refs

        self.title("新建方案" if mode == "create" else "编辑方案")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.minsize(480, 420)

        self._build_ui()
        self._populate_form()

        self.update_idletasks()
        px = parent.winfo_rootx() + 60
        py = parent.winfo_rooty() + 40
        self.geometry(f"+{px}+{py}")

    # ── UI ─────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        main = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=8)
        main.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # ── Form fields (all explicit font) ──────────────────────
        form = ctk.CTkFrame(main, fg_color="transparent")
        form.pack(fill=ctk.X)

        _f12b = _df(12, bold=True)  # label bold 12pt
        _f12 = _df(12)              # entry / regular 12pt

        ctk.CTkLabel(form, text="方案名称:", font=_f12b,
                      text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=3)
        self._name_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self._name_var, font=_f12,
                      corner_radius=6, border_color=BORDER,
                      ).grid(row=0, column=1, sticky="ew", pady=3, padx=(8, 0))

        ctk.CTkLabel(form, text="描述:", font=_f12b,
                      text_color=TEXT_PRIMARY).grid(row=1, column=0, sticky="w", pady=3)
        self._desc_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self._desc_var, font=_f12,
                      corner_radius=6, border_color=BORDER,
                      ).grid(row=1, column=1, sticky="ew", pady=3, padx=(8, 0))

        ctk.CTkLabel(form, text="启动热键:", font=_f12b,
                      text_color=TEXT_PRIMARY).grid(row=2, column=0, sticky="w", pady=3)
        self._start_var = ctk.StringVar(value="F10")
        ctk.CTkEntry(form, textvariable=self._start_var, font=_f12,
                      corner_radius=6, border_color=BORDER,
                      ).grid(row=2, column=1, sticky="ew", pady=3, padx=(8, 0))

        ctk.CTkLabel(form, text="停止热键:", font=_f12b,
                      text_color=TEXT_PRIMARY).grid(row=3, column=0, sticky="w", pady=3)
        self._stop_var = ctk.StringVar(value="F12")
        ctk.CTkEntry(form, textvariable=self._stop_var, font=_f12,
                      corner_radius=6, border_color=BORDER,
                      ).grid(row=3, column=1, sticky="ew", pady=3, padx=(8, 0))

        self._loop_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(form, text="循环执行", variable=self._loop_var,
                         font=_f12, corner_radius=4,
                         ).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        form.columnconfigure(1, weight=1)

        # ── Action list (ultra-compact) ─────────────────────────
        ctk.CTkLabel(main, text="操作步骤", font=_f12b,
                      text_color=TEXT_PRIMARY,
                      ).pack(anchor="w", pady=(8, 3))

        self._action_container = ctk.CTkScrollableFrame(
            main, fg_color="#FAFBFC", corner_radius=6,
            border_width=1, border_color=BORDER,
            scrollbar_fg_color="#FAFBFC",
            scrollbar_button_color="#CED4DA",
            scrollbar_button_hover_color=ACCENT_BLUE,
        )
        self._action_container.pack(fill=ctk.BOTH, expand=True, pady=(0, 6))

        # ── Action toolbar ───────────────────────────────────────
        act_bar = ctk.CTkFrame(main, fg_color="transparent")
        act_bar.pack(fill=ctk.X)

        _btn_font = _df(12)
        for txt, cmd in [
            ("添加步骤", self._on_add), ("编辑", self._on_edit),
            ("删除", self._on_delete), ("上移", self._on_move_up),
            ("下移", self._on_move_down),
        ]:
            ctk.CTkButton(act_bar, text=txt, command=cmd,
                           font=_btn_font, **BTN_DEFAULT,
                           ).pack(side=ctk.LEFT, padx=1)

        # ── Bottom buttons ───────────────────────────────────────
        bottom = ctk.CTkFrame(main, fg_color="transparent")
        bottom.pack(fill=ctk.X, pady=(4, 0))
        ctk.CTkButton(bottom, text="保存", command=self._on_save,
                       font=_f12b, **BTN_PRIMARY,
                       ).pack(side=ctk.RIGHT, padx=(4, 0))
        ctk.CTkButton(bottom, text="取消", command=self._on_cancel,
                       font=_f12, **BTN_DEFAULT,
                       ).pack(side=ctk.RIGHT)

    def _populate_form(self) -> None:
        if self._initial_scheme is not None:
            s = self._initial_scheme
            self._name_var.set(s.name)
            self._desc_var.set(s.description)
            self._start_var.set(s.start_hotkey)
            self._stop_var.set(s.stop_hotkey)
            self._loop_var.set(s.loop)
        self._refresh_action_list()

    # ── Action list — build once, then just recolor on selection ──

    def _refresh_action_list(self) -> None:
        """(Re)build the action list from scratch.  Called only when the
        list of actions changes (add / edit / delete / move)."""
        for w in self._action_container.winfo_children():
            w.destroy()
        self._item_widgets.clear()

        _f11 = _df(11)
        _f9 = _df(9)

        for i, action in enumerate(self._actions):
            # Frame
            frame = ctk.CTkFrame(self._action_container, height=28,
                                 fg_color="transparent", corner_radius=3)
            frame.pack(fill=ctk.X, padx=1, pady=0)
            frame.pack_propagate(False)

            # Left bar
            bar = ctk.CTkFrame(frame, width=3, corner_radius=0,
                               fg_color="transparent")
            bar.pack(side=ctk.LEFT, fill=ctk.Y)

            # Badge
            badge = ctk.CTkFrame(frame, width=20, height=20,
                                 corner_radius=10, fg_color="#DEE2E6")
            badge.pack(side=ctk.LEFT, padx=(5, 4))
            badge.pack_propagate(False)
            num_lbl = ctk.CTkLabel(badge, text=str(i + 1), font=_f9,
                                    text_color=TEXT_PRIMARY)
            num_lbl.place(relx=0.5, rely=0.5, anchor="center")

            # Description
            desc = ctk.CTkLabel(frame, text=str(action), font=_f11,
                                 text_color=TEXT_PRIMARY, anchor="w")
            desc.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

            self._item_widgets.append({
                "frame": frame, "bar": bar, "badge": badge,
                "num_lbl": num_lbl, "desc": desc, "action": action,
            })

            for w in (frame, desc, badge):
                w.bind("<Button-1>", lambda e, i=i: self._select_action(i))

        self._apply_selection()

    def _apply_selection(self) -> None:
        """Update visual state of ALL items by comparing against
        ``_selected_action_idx``.  O(1) per item — no destroy/create."""
        for idx, item in enumerate(self._item_widgets):
            sel = idx == self._selected_action_idx
            item["frame"].configure(fg_color="#E3F2FD" if sel else "transparent")
            item["bar"].configure(fg_color=ACCENT_BLUE if sel else "transparent")
            item["badge"].configure(fg_color=ACCENT_BLUE if sel else "#DEE2E6")
            item["num_lbl"].configure(
                text_color="white" if sel else TEXT_PRIMARY)

    def _select_action(self, idx: int) -> None:
        """Selection changed — just recolor the two affected items."""
        if self._selected_action_idx == idx:
            return  # no change
        # Mark previous and new selection for visual update
        self._selected_action_idx = idx
        self._apply_selection()

    # ── Action CRUD ──────────────────────────────────────────────

    def _on_add(self) -> None:
        action = self._open_action_dialog()
        if action is not None:
            action = self._replace_order(action, len(self._actions) + 1)
            self._actions.append(action)
            self._selected_action_idx = len(self._actions) - 1
            self._refresh_action_list()

    def _on_edit(self) -> None:
        if self._selected_action_idx is None:
            messagebox.showwarning("提示", "请先选择一个步骤", parent=self); return
        idx = self._selected_action_idx
        action = self._open_action_dialog(action=self._actions[idx])
        if action is not None:
            action = self._replace_order(action, self._actions[idx].order)
            self._actions[idx] = action
            self._refresh_action_list()

    def _on_delete(self) -> None:
        if self._selected_action_idx is None:
            messagebox.showwarning("提示", "请先选择一个步骤", parent=self); return
        del self._actions[self._selected_action_idx]
        self._selected_action_idx = None
        self._renumber()
        self._refresh_action_list()

    def _on_move_up(self) -> None:
        if self._selected_action_idx is None or self._selected_action_idx == 0:
            return
        i = self._selected_action_idx
        self._actions[i], self._actions[i - 1] = self._actions[i - 1], self._actions[i]
        self._selected_action_idx = i - 1
        self._renumber()
        self._refresh_action_list()

    def _on_move_down(self) -> None:
        if self._selected_action_idx is None or self._selected_action_idx >= len(self._actions) - 1:
            return
        i = self._selected_action_idx
        self._actions[i], self._actions[i + 1] = self._actions[i + 1], self._actions[i]
        self._selected_action_idx = i + 1
        self._renumber()
        self._refresh_action_list()

    @staticmethod
    def _replace_order(action: Action, new_order: int) -> Action:
        if action.order == new_order:
            return action
        return Action(
            action_type=action.action_type, order=new_order,
            key=action.key, mouse_button=action.mouse_button,
            duration=action.duration, wait_seconds=action.wait_seconds,
            wait_min=action.wait_min, wait_max=action.wait_max,
        )

    def _renumber(self) -> None:
        for i in range(len(self._actions)):
            self._actions[i] = self._replace_order(self._actions[i], i + 1)

    # ── Action sub-dialog (flattened + spacious) ────────────────

    def _open_action_dialog(self, action: Action | None = None) -> Action | None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("添加步骤" if action is None else "编辑步骤")
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)
        result_holder: list[Action | None] = [None]

        _f12b = _df(12, bold=True)
        _f12 = _df(12)

        outer = ctk.CTkFrame(dlg, fg_color="#FFFFFF", corner_radius=8)
        outer.pack(fill=ctk.BOTH, expand=True, padx=14, pady=14)

        # ── Type selector ────────────────────────────────────────
        type_row = ctk.CTkFrame(outer, fg_color="transparent")
        type_row.pack(fill=ctk.X, pady=(0, 10))

        ctk.CTkLabel(type_row, text="操作类型:", font=_f12b,
                      text_color=TEXT_PRIMARY).pack(side=ctk.LEFT)

        default_type = _action_to_ui_type(action) if action else "按键"
        type_var = ctk.StringVar(value=default_type)

        # Flattened OptionMenu — no 3D, light background, blue hover
        ctk.CTkOptionMenu(type_row, variable=type_var,
            values=["按键", "鼠标点击", "固定等待", "随机等待"],
            font=_f12, dropdown_font=_f12,
            corner_radius=6,
            fg_color="#F8F9FA",
            button_color="#F8F9FA",
            text_color=TEXT_PRIMARY,
            dropdown_fg_color="white",
            dropdown_hover_color="#E3F2FD",
            dropdown_text_color=TEXT_PRIMARY,
        ).pack(side=ctk.LEFT, padx=(10, 0))

        # ── Dynamic fields ───────────────────────────────────────
        fields = ctk.CTkFrame(outer, fg_color="#FAFBFC", corner_radius=6)
        fields.pack(fill=ctk.X, pady=(0, 10))

        _ENTRY_W = 100  # pixel width for all sub-dialog entries

        # -- Key press --
        kp = ctk.CTkFrame(fields, fg_color="transparent")
        ctk.CTkLabel(kp, text="按键:", font=_f12).pack(side=ctk.LEFT)
        kp_key = ctk.CTkEntry(kp, font=_f12, width=_ENTRY_W,
                               corner_radius=6, border_color=BORDER)
        kp_key.pack(side=ctk.LEFT, padx=(8, 14))
        kp_key.insert(0, action.key if action and action.key else "Space")
        ctk.CTkLabel(kp, text="持续时间:", font=_f12).pack(side=ctk.LEFT)
        kp_dur = ctk.CTkEntry(kp, font=_f12, width=_ENTRY_W,
                               corner_radius=6, border_color=BORDER)
        kp_dur.pack(side=ctk.LEFT, padx=(8, 0))
        kp_dur.insert(0, str(action.duration) if action and action.action_type == ActionType.KEY_PRESS else "0.1")

        # -- Mouse click --
        mc = ctk.CTkFrame(fields, fg_color="transparent")
        mc_btn_var = ctk.StringVar(
            value="左键" if action and action.mouse_button == MouseButton.LEFT else "右键")
        ctk.CTkRadioButton(mc, text="左键", variable=mc_btn_var,
                            value="左键", font=_f12).pack(side=ctk.LEFT)
        ctk.CTkRadioButton(mc, text="右键", variable=mc_btn_var,
                            value="右键", font=_f12).pack(side=ctk.LEFT, padx=(8, 0))
        ctk.CTkLabel(mc, text="  持续时间:", font=_f12).pack(side=ctk.LEFT, padx=(14, 0))
        mc_dur = ctk.CTkEntry(mc, font=_f12, width=_ENTRY_W,
                               corner_radius=6, border_color=BORDER)
        mc_dur.pack(side=ctk.LEFT, padx=(8, 0))
        mc_dur.insert(0, str(action.duration) if action and action.action_type == ActionType.MOUSE_CLICK else "0.1")

        # -- Fixed wait --
        fw = ctk.CTkFrame(fields, fg_color="transparent")
        ctk.CTkLabel(fw, text="等待秒数:", font=_f12).pack(side=ctk.LEFT)
        fw_sec = ctk.CTkEntry(fw, font=_f12, width=_ENTRY_W,
                               corner_radius=6, border_color=BORDER)
        fw_sec.pack(side=ctk.LEFT, padx=(8, 0))
        fw_sec.insert(0, str(action.wait_seconds) if action and action.wait_seconds is not None else "1.0")

        # -- Random wait --
        rw = ctk.CTkFrame(fields, fg_color="transparent")
        ctk.CTkLabel(rw, text="最小秒数:", font=_f12).pack(side=ctk.LEFT)
        rw_min = ctk.CTkEntry(rw, font=_f12, width=80,
                               corner_radius=6, border_color=BORDER)
        rw_min.pack(side=ctk.LEFT, padx=(8, 0))
        rw_min.insert(0, str(action.wait_min) if action and action.wait_min is not None else "1.0")
        ctk.CTkLabel(rw, text="  最大秒数:", font=_f12).pack(side=ctk.LEFT, padx=(14, 0))
        rw_max = ctk.CTkEntry(rw, font=_f12, width=80,
                               corner_radius=6, border_color=BORDER)
        rw_max.pack(side=ctk.LEFT, padx=(8, 0))
        rw_max.insert(0, str(action.wait_max) if action and action.wait_max is not None else "3.0")

        all_frames = {"按键": kp, "鼠标点击": mc, "固定等待": fw, "随机等待": rw}

        def show_fields(ui_type: str) -> None:
            for f in all_frames.values():
                f.pack_forget()
            if ui_type in all_frames:
                all_frames[ui_type].pack(fill=ctk.X, padx=10, pady=8)

        type_var.trace_add("write", lambda *_: show_fields(type_var.get()))
        show_fields(type_var.get())

        def build_action() -> Action | None:
            ui = type_var.get()
            order = action.order if action is not None else 0
            try:
                if ui == "按键":
                    return Action.key_press(key=kp_key.get().strip() or "Space",
                                            order=order,
                                            duration=_safe_float(kp_dur.get(), 0.1))
                if ui == "鼠标点击":
                    btn = MouseButton.LEFT if mc_btn_var.get() == "左键" else MouseButton.RIGHT
                    return Action.mouse_click(button=btn, order=order,
                                              duration=_safe_float(mc_dur.get(), 0.1))
                if ui == "固定等待":
                    return Action.wait_fixed(seconds=_safe_float(fw_sec.get(), 1.0), order=order)
                if ui == "随机等待":
                    return Action.wait_random(min_s=_safe_float(rw_min.get(), 1.0),
                                              max_s=_safe_float(rw_max.get(), 3.0), order=order)
                return None
            except ValueError as exc:
                messagebox.showerror("参数错误", str(exc), parent=dlg); return None

        def on_ok() -> None:
            built = build_action()
            if built is not None:
                result_holder[0] = built
                dlg.destroy()

        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill=ctk.X, pady=(4, 0))
        ctk.CTkButton(btn_row, text="确定", command=on_ok,
                       font=_f12b, **BTN_PRIMARY,
                       ).pack(side=ctk.RIGHT, padx=(6, 0))
        ctk.CTkButton(btn_row, text="取消", command=dlg.destroy,
                       font=_f12, **BTN_DEFAULT,
                       ).pack(side=ctk.RIGHT)

        dlg.update_idletasks()
        dlg.geometry(f"+{self.winfo_rootx() + 80}+{self.winfo_rooty() + 80}")

        self.wait_window(dlg)
        return result_holder[0]

    # ── Save / Cancel ────────────────────────────────────────────

    def _on_save(self) -> None:
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror("验证失败", "方案名称不能为空", parent=self); return
        if not self._actions:
            messagebox.showerror("验证失败", "至少需要一个操作步骤", parent=self); return

        start = self._start_var.get().strip()
        stop = self._stop_var.get().strip()
        if not start or not stop:
            messagebox.showerror("验证失败", "热键不能为空", parent=self); return
        if start == stop:
            messagebox.showerror("验证失败", "启停热键不能相同", parent=self); return

        desc = self._desc_var.get().strip()
        loop = self._loop_var.get()

        if self._mode == "edit" and self._initial_scheme is not None and not self._initial_scheme.is_preset:
            scheme = Scheme(id=self._initial_scheme.id, name=name, description=desc,
                            actions=tuple(self._actions), loop=loop,
                            start_hotkey=start, stop_hotkey=stop, is_preset=False)
        else:
            scheme = Scheme.create(name=name, description=desc,
                                   actions=tuple(self._actions), loop=loop,
                                   start_hotkey=start, stop_hotkey=stop)
        self.result = scheme
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()

    def get_result(self) -> Scheme | None:
        return self.result


# ── Helper ──────────────────────────────────────────────────────────

def _safe_float(raw: str, default: float) -> float:
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default
