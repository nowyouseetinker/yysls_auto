from __future__ import annotations

import customtkinter as ctk
from typing import TYPE_CHECKING, Any

from models.enums import ActionType
from ui.theme import (
    ACCENT_BLUE,
    ACCENT_ORANGE,
    BORDER,
    FONT_FAMILY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    label_font,
)

if TYPE_CHECKING:
    from models.scheme import Scheme
    from models.action import Action


class StepPreviewWidget(ctk.CTkFrame):
    """Step preview — Microsoft YaHei 10pt, syntax highlighting."""

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs: Any) -> None:
        super().__init__(
            parent,
            fg_color="#FFFFFF",
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )

        self._title = ctk.CTkLabel(
            self, text="操作步骤预览", font=label_font(),
            text_color=TEXT_PRIMARY, anchor="w",
        )
        self._title.pack(fill=ctk.X, padx=10, pady=(6, 3))

        # Explicit Microsoft YaHei 10pt — no monospace
        body_font = ctk.CTkFont(family=FONT_FAMILY, size=13)
        self._text = ctk.CTkTextbox(
            self,
            corner_radius=6,
            fg_color="#FAFBFC",
            border_width=1,
            border_color=BORDER,
            font=body_font,
            wrap="word",
            activate_scrollbars=True,
        )
        self._text.pack(fill=ctk.BOTH, expand=True, padx=8, pady=(0, 5))

        # Color-only tags (CTkTextbox forbids font in tag_config)
        self._text.tag_config("step_num", foreground=ACCENT_BLUE)
        self._text.tag_config("key_name", foreground=ACCENT_BLUE)
        self._text.tag_config("time_val", foreground=ACCENT_ORANGE)
        self._text.tag_config("normal", foreground=TEXT_PRIMARY)
        self._text.tag_config("dim", foreground=TEXT_SECONDARY)

        self._text.configure(state="disabled")

    def set_scheme(self, scheme: Scheme) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        for i, action in enumerate(scheme.actions):
            self._insert_action_line(i + 1, action)
        self._text.configure(state="disabled")
        self._text.see("1.0")

    def clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    def _insert_action_line(self, idx: int, action: Action) -> None:
        self._text.insert("end", f"{idx}.  ", "step_num")

        if action.action_type == ActionType.KEY_PRESS:
            self._text.insert("end", "按键  ", "normal")
            self._text.insert("end", action.key, "key_name")
            self._text.insert("end", f"  ({action.duration}s)", "time_val")

        elif action.action_type == ActionType.MOUSE_CLICK:
            btn = "左键" if action.mouse_button == "left" else "右键"
            self._text.insert("end", f"鼠标{btn}点击  ", "normal")
            self._text.insert("end", f"({action.duration}s)", "time_val")

        elif action.action_type == ActionType.WAIT:
            self._text.insert("end", "等待  ", "normal")
            if action.wait_seconds is not None:
                self._text.insert("end", f"{action.wait_seconds}", "time_val")
                self._text.insert("end", " 秒", "normal")
            else:
                self._text.insert("end", f"{action.wait_min}", "time_val")
                self._text.insert("end", " ~ ", "dim")
                self._text.insert("end", f"{action.wait_max}", "time_val")
                self._text.insert("end", " 秒", "normal")

        self._text.insert("end", "\n")
