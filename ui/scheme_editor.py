from __future__ import annotations

import tkinter as tk
import uuid
from tkinter import messagebox, ttk

from models.action import Action
from models.enums import ActionType, MouseButton
from models.scheme import Scheme

# ── type-to-ui mapping ──────────────────────────────────────────────


def _action_to_ui_type(action: Action) -> str:
    """Map an Action to the corresponding UI type label."""
    if action.action_type == ActionType.KEY_PRESS:
        return "按键"
    if action.action_type == ActionType.MOUSE_CLICK:
        return "鼠标点击"
    if action.action_type == ActionType.WAIT:
        if action.wait_seconds is not None:
            return "固定等待"
        return "随机等待"
    return "按键"  # type: ignore[unreachable]


# ── scheme editor ───────────────────────────────────────────────────


class SchemeEditorWindow(tk.Toplevel):
    """Modal dialog for creating or editing a :class:`Scheme`.

    Usage::

        dialog = SchemeEditorWindow(parent, mode="create")
        parent.wait_window(dialog)
        scheme = dialog.get_result()  # Scheme or None if cancelled

        dialog = SchemeEditorWindow(parent, mode="edit", scheme=existing)
        parent.wait_window(dialog)
        result = dialog.get_result()
    """

    def __init__(
        self,
        parent: tk.Widget,
        mode: str = "create",
        scheme: Scheme | None = None,
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self.result: Scheme | None = None

        # ── handle preset editing: create a copy ────────────────
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

        # ── window setup ─────────────────────────────────────────
        self.title("新建方案" if mode == "create" else "编辑方案")
        self.transient(parent)  # type: ignore[call-overload]
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.resizable(True, True)

        self._build_ui()
        self._populate_form()

        # Center near parent
        self.update_idletasks()
        px = parent.winfo_rootx() + 50
        py = parent.winfo_rooty() + 50
        self.geometry(f"+{px}+{py}")

    # ── UI construction ─────────────────────────────────────────

    def _build_ui(self) -> None:
        """Create all form widgets and layout."""
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # --- form fields row ---
        form = ttk.Frame(main)
        form.pack(fill=tk.X)

        # name
        ttk.Label(form, text="方案名称:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self._name_var = tk.StringVar()
        self._name_entry = ttk.Entry(
            form, textvariable=self._name_var, width=30
        )
        self._name_entry.grid(
            row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0)
        )

        # description
        ttk.Label(form, text="描述:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self._desc_var = tk.StringVar()
        self._desc_entry = ttk.Entry(
            form, textvariable=self._desc_var, width=30
        )
        self._desc_entry.grid(
            row=1, column=1, sticky=tk.EW, pady=2, padx=(5, 0)
        )

        # start hotkey
        ttk.Label(form, text="启动热键:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self._start_var = tk.StringVar(value="F10")
        self._start_entry = ttk.Entry(
            form, textvariable=self._start_var, width=15
        )
        self._start_entry.grid(
            row=2, column=1, sticky=tk.W, pady=2, padx=(5, 0)
        )

        # stop hotkey
        ttk.Label(form, text="停止热键:").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self._stop_var = tk.StringVar(value="F12")
        self._stop_entry = ttk.Entry(
            form, textvariable=self._stop_var, width=15
        )
        self._stop_entry.grid(
            row=3, column=1, sticky=tk.W, pady=2, padx=(5, 0)
        )

        # loop checkbox
        self._loop_var = tk.BooleanVar(value=True)
        self._loop_cb = ttk.Checkbutton(
            form, text="循环执行", variable=self._loop_var
        )
        self._loop_cb.grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=2
        )

        form.columnconfigure(1, weight=1)

        # --- action list ---
        list_frame = ttk.LabelFrame(main, text="操作步骤", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 5))

        list_inner = ttk.Frame(list_frame)
        list_inner.pack(fill=tk.BOTH, expand=True)

        self._listbox = tk.Listbox(
            list_inner, height=8, exportselection=False
        )
        scrollbar = ttk.Scrollbar(
            list_inner, orient=tk.VERTICAL, command=self._listbox.yview
        )
        self._listbox.configure(yscrollcommand=scrollbar.set)

        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- action toolbar ---
        toolbar = ttk.Frame(main)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        self._add_btn = ttk.Button(
            toolbar, text="添加步骤", command=self._on_add
        )
        self._add_btn.pack(side=tk.LEFT, padx=(0, 2))

        self._edit_btn = ttk.Button(
            toolbar, text="编辑", command=self._on_edit
        )
        self._edit_btn.pack(side=tk.LEFT, padx=2)

        self._delete_btn = ttk.Button(
            toolbar, text="删除", command=self._on_delete
        )
        self._delete_btn.pack(side=tk.LEFT, padx=2)

        self._move_up_btn = ttk.Button(
            toolbar, text="上移", command=self._on_move_up
        )
        self._move_up_btn.pack(side=tk.LEFT, padx=2)

        self._move_down_btn = ttk.Button(
            toolbar, text="下移", command=self._on_move_down
        )
        self._move_down_btn.pack(side=tk.LEFT, padx=2)

        # --- bottom buttons ---
        bottom = ttk.Frame(main)
        bottom.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(bottom, text="保存", command=self._on_save).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(bottom, text="取消", command=self._on_cancel).pack(
            side=tk.RIGHT
        )

    def _populate_form(self) -> None:
        """Pre-fill form fields from the initial scheme (edit mode)."""
        if self._initial_scheme is not None:
            s = self._initial_scheme
            self._name_var.set(s.name)
            self._desc_var.set(s.description)
            self._start_var.set(s.start_hotkey)
            self._stop_var.set(s.stop_hotkey)
            self._loop_var.set(s.loop)
        self._refresh_listbox()

    # ── listbox helpers ─────────────────────────────────────────

    def _refresh_listbox(self) -> None:
        """Rebuild the Listbox contents from ``self._actions``."""
        self._listbox.delete(0, tk.END)
        for a in self._actions:
            self._listbox.insert(tk.END, str(a))

    def _selected_index(self) -> int | None:
        """Return the currently selected action index, or *None*."""
        sel = self._listbox.curselection()  # type: ignore[no-untyped-call]
        if not sel:
            return None
        return int(sel[0])

    # ── action CRUD callbacks ───────────────────────────────────

    def _on_add(self) -> None:
        """Open the action sub-dialog to append a new step."""
        action = self._open_action_dialog(action=None)
        if action is not None:
            new_order = len(self._actions) + 1
            action = self._replace_order(action, new_order)
            self._actions.append(action)
            self._refresh_listbox()

    def _on_edit(self) -> None:
        """Open the action sub-dialog to modify the selected step."""
        idx = self._selected_index()
        if idx is None:
            messagebox.showwarning(
                "提示", "请先选择要编辑的步骤", parent=self
            )
            return
        action = self._open_action_dialog(action=self._actions[idx])
        if action is not None:
            action = self._replace_order(action, self._actions[idx].order)
            self._actions[idx] = action
            self._refresh_listbox()

    def _on_delete(self) -> None:
        """Remove the selected step and re-number remaining ones."""
        idx = self._selected_index()
        if idx is None:
            messagebox.showwarning(
                "提示", "请先选择要删除的步骤", parent=self
            )
            return
        del self._actions[idx]
        self._renumber_actions()
        self._refresh_listbox()

    def _on_move_up(self) -> None:
        """Swap the selected step with the one above it."""
        idx = self._selected_index()
        if idx is None or idx == 0:
            return
        self._actions[idx], self._actions[idx - 1] = (
            self._actions[idx - 1],
            self._actions[idx],
        )
        self._renumber_actions()
        self._refresh_listbox()
        self._listbox.selection_set(idx - 1)

    def _on_move_down(self) -> None:
        """Swap the selected step with the one below it."""
        idx = self._selected_index()
        if idx is None or idx >= len(self._actions) - 1:
            return
        self._actions[idx], self._actions[idx + 1] = (
            self._actions[idx + 1],
            self._actions[idx],
        )
        self._renumber_actions()
        self._refresh_listbox()
        self._listbox.selection_set(idx + 1)

    # ── helpers ─────────────────────────────────────────────────

    @staticmethod
    def _replace_order(action: Action, new_order: int) -> Action:
        """Return a new Action with ``order`` replaced."""
        if action.order == new_order:
            return action
        # Use frozen-dataclass positional construction via the
        # internal __init__ so we preserve all per-type field combos.
        return Action(
            action_type=action.action_type,
            order=new_order,
            key=action.key,
            mouse_button=action.mouse_button,
            duration=action.duration,
            wait_seconds=action.wait_seconds,
            wait_min=action.wait_min,
            wait_max=action.wait_max,
        )

    def _renumber_actions(self) -> None:
        """Re-assign order numbers 1..N to all actions in-place."""
        for i in range(len(self._actions)):
            self._actions[i] = self._replace_order(self._actions[i], i + 1)

    # ── action sub-dialog ───────────────────────────────────────

    # The sub-dialog is split into a builder (testable) and a
    # waiter that blocks until the dialog is closed.

    def _open_action_dialog(
        self, action: Action | None = None
    ) -> Action | None:
        """Build, show and wait for the add/edit action sub-dialog.

        Args:
            action: If provided, pre-fill the dialog for editing;
                    otherwise create a new action from scratch.

        Returns:
            A validated :class:`Action` if the user confirmed,
            or *None* if they cancelled.
        """
        dlg, holder = self._build_action_subdialog(action)
        self.wait_window(dlg)
        return holder[0]

    def _build_action_subdialog(
        self, action: Action | None = None
    ) -> tuple[tk.Toplevel, list[Action | None]]:
        """Build the add/edit action Toplevel **without** entering the
        event loop.

        Args:
            action: Optional existing action to pre-fill.

        Returns:
            ``(dialog, result_holder)`` where ``result_holder`` is a
            single-element list that will contain the :class:`Action` or
            *None* once the user closes the dialog.
        """
        dlg = tk.Toplevel(self)
        dlg.title("添加步骤" if action is None else "编辑步骤")
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)
        holder: list[Action | None] = [None]

        outer = ttk.Frame(dlg, padding=10)
        outer.pack(fill=tk.BOTH)

        # --- type selector ---
        type_row = ttk.Frame(outer)
        type_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(type_row, text="操作类型:").pack(side=tk.LEFT)

        default_type = _action_to_ui_type(action) if action else "按键"
        type_var = tk.StringVar(value=default_type)
        type_labels = ["按键", "鼠标点击", "固定等待", "随机等待"]
        ttk.OptionMenu(
            type_row,
            type_var,
            default_type,
            *type_labels,
        ).pack(side=tk.LEFT, padx=(5, 0))

        # --- dynamic fields container ---
        fields = ttk.Frame(outer)
        fields.pack(fill=tk.X, pady=(0, 10))

        # -- key press fields --
        kp_frame = ttk.Frame(fields)
        ttk.Label(kp_frame, text="按键:").pack(side=tk.LEFT)
        kp_key_var = tk.StringVar(value="Space")
        ttk.Entry(kp_frame, textvariable=kp_key_var, width=12).pack(
            side=tk.LEFT, padx=(5, 10)
        )
        ttk.Label(kp_frame, text="持续时间:").pack(side=tk.LEFT)
        kp_dur_var = tk.StringVar(value="0.1")
        ttk.Entry(kp_frame, textvariable=kp_dur_var, width=8).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # -- mouse click fields --
        mc_frame = ttk.Frame(fields)
        mc_btn_var = tk.StringVar(value="左键")
        ttk.Radiobutton(
            mc_frame, text="左键", variable=mc_btn_var, value="左键"
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            mc_frame, text="右键", variable=mc_btn_var, value="右键"
        ).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(mc_frame, text="  持续时间:").pack(side=tk.LEFT)
        mc_dur_var = tk.StringVar(value="0.1")
        ttk.Entry(mc_frame, textvariable=mc_dur_var, width=8).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # -- fixed wait fields --
        fw_frame = ttk.Frame(fields)
        ttk.Label(fw_frame, text="等待秒数:").pack(side=tk.LEFT)
        fw_sec_var = tk.StringVar(value="1.0")
        ttk.Entry(fw_frame, textvariable=fw_sec_var, width=10).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # -- random wait fields --
        rw_frame = ttk.Frame(fields)
        ttk.Label(rw_frame, text="最小秒数:").pack(side=tk.LEFT)
        rw_min_var = tk.StringVar(value="1.0")
        ttk.Entry(rw_frame, textvariable=rw_min_var, width=8).pack(
            side=tk.LEFT, padx=(5, 0)
        )
        ttk.Label(rw_frame, text="  最大秒数:").pack(side=tk.LEFT, padx=(10, 0))
        rw_max_var = tk.StringVar(value="3.0")
        ttk.Entry(rw_frame, textvariable=rw_max_var, width=8).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        all_field_frames: list[ttk.Frame] = [
            kp_frame,
            mc_frame,
            fw_frame,
            rw_frame,
        ]

        # -- type-switching logic --
        def _show_fields(ui_type: str) -> None:
            for f in all_field_frames:
                f.pack_forget()
            mapping: dict[str, ttk.Frame] = {
                "按键": kp_frame,
                "鼠标点击": mc_frame,
                "固定等待": fw_frame,
                "随机等待": rw_frame,
            }
            target = mapping.get(ui_type)
            if target is not None:
                target.pack(fill=tk.X)

        # Keep a reference so the trace callback doesn't get gc'd.
        self.__type_cb_name = type_var.trace_add(
            "write", lambda *_: _show_fields(type_var.get())
        )

        # -- pre-fill when editing --
        if action is not None:
            if action.action_type == ActionType.KEY_PRESS:
                kp_key_var.set(action.key or "Space")
                kp_dur_var.set(str(action.duration))
            elif action.action_type == ActionType.MOUSE_CLICK:
                mc_btn_var.set(
                    "左键"
                    if action.mouse_button == MouseButton.LEFT
                    else "右键"
                )
                mc_dur_var.set(str(action.duration))
            elif action.action_type == ActionType.WAIT:
                if action.wait_seconds is not None:
                    fw_sec_var.set(str(action.wait_seconds))
                else:
                    rw_min_var.set(str(action.wait_min or 1.0))
                    rw_max_var.set(str(action.wait_max or 3.0))

        _show_fields(type_var.get())

        # -- action builders (called on OK) --
        def _build_action() -> Action | None:
            ui = type_var.get()
            order = action.order if action is not None else 0
            try:
                if ui == "按键":
                    return Action.key_press(
                        key=kp_key_var.get().strip() or "Space",
                        order=order,
                        duration=_safe_float(kp_dur_var.get(), 0.1),
                    )
                if ui == "鼠标点击":
                    btn = (
                        MouseButton.LEFT
                        if mc_btn_var.get() == "左键"
                        else MouseButton.RIGHT
                    )
                    return Action.mouse_click(
                        button=btn,
                        order=order,
                        duration=_safe_float(mc_dur_var.get(), 0.1),
                    )
                if ui == "固定等待":
                    return Action.wait_fixed(
                        seconds=_safe_float(fw_sec_var.get(), 1.0),
                        order=order,
                    )
                if ui == "随机等待":
                    return Action.wait_random(
                        min_s=_safe_float(rw_min_var.get(), 1.0),
                        max_s=_safe_float(rw_max_var.get(), 3.0),
                        order=order,
                    )
                return None
            except ValueError as exc:
                messagebox.showerror(
                    "参数错误", str(exc), parent=dlg
                )
                return None

        # --- OK / Cancel ---
        def _on_ok() -> None:
            built = _build_action()
            if built is not None:
                holder[0] = built
                dlg.destroy()

        def _on_cancel_sub() -> None:
            holder[0] = None
            dlg.destroy()

        btn_row = ttk.Frame(outer)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="确定", command=_on_ok).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(btn_row, text="取消", command=_on_cancel_sub).pack(
            side=tk.RIGHT
        )

        # Center sub-dialog
        dlg.update_idletasks()
        cx = self.winfo_rootx() + 80
        cy = self.winfo_rooty() + 80
        dlg.geometry(f"+{cx}+{cy}")

        return dlg, holder

    # ── save / cancel ───────────────────────────────────────────

    def _on_save(self) -> None:
        """Validate form values, build a Scheme, store in ``result``,
        and close the dialog."""
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror(
                "验证失败", "方案名称不能为空", parent=self
            )
            return

        if not self._actions:
            messagebox.showerror(
                "验证失败", "至少需要一个操作步骤", parent=self
            )
            return

        start = self._start_var.get().strip()
        stop = self._stop_var.get().strip()
        if not start:
            messagebox.showerror(
                "验证失败", "启动热键不能为空", parent=self
            )
            return
        if not stop:
            messagebox.showerror(
                "验证失败", "停止热键不能为空", parent=self
            )
            return
        if start == stop:
            messagebox.showerror(
                "验证失败", "启动热键和停止热键不能相同", parent=self
            )
            return

        desc = self._desc_var.get().strip()
        loop = self._loop_var.get()

        if (
            self._mode == "edit"
            and self._initial_scheme is not None
            and not self._initial_scheme.is_preset
        ):
            # Preserve the original id for non-preset edits.
            scheme = Scheme(
                id=self._initial_scheme.id,
                name=name,
                description=desc,
                actions=tuple(self._actions),
                loop=loop,
                start_hotkey=start,
                stop_hotkey=stop,
                is_preset=False,
            )
        else:
            scheme = Scheme.create(
                name=name,
                description=desc,
                actions=tuple(self._actions),
                loop=loop,
                start_hotkey=start,
                stop_hotkey=stop,
            )

        self.result = scheme
        self.destroy()

    def _on_cancel(self) -> None:
        """Close the dialog without saving."""
        self.result = None
        self.destroy()

    # ── public API ──────────────────────────────────────────────

    def get_result(self) -> Scheme | None:
        """Return the created/edited :class:`Scheme`, or *None* if
        cancelled."""
        return self.result


# ── helpers ─────────────────────────────────────────────────────────


def _safe_float(raw: str, default: float) -> float:
    """Parse *raw* to float, falling back to *default* on failure."""
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default
