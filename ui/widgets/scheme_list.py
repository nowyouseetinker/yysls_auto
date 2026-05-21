from __future__ import annotations

import customtkinter as ctk
from typing import Any

from models.scheme import Scheme
from ui.theme import (
    ACCENT_BLUE,
    ACCENT_BLUE_HOVER,
    BG_CARD,
    BG_HOVER,
    BG_SELECTED,
    BORDER,
    FONT_FAMILY,
    TEXT_PRIMARY,
)


class _SchemeItem(ctk.CTkFrame):
    """Compact list item — fixed height 36px, zero excess padding."""

    def __init__(
        self,
        parent: ctk.CTkScrollableFrame,
        scheme: Scheme,
        index: int,
        on_click: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, height=36, **kwargs)
        self.pack_propagate(False)

        self._scheme = scheme
        self._index = index
        self._on_click = on_click
        self._selected = False

        # Left indicator bar (visible when selected)
        self._indicator = ctk.CTkFrame(
            self, width=3, corner_radius=0, fg_color="transparent"
        )
        self._indicator.pack(side=ctk.LEFT, fill=ctk.Y)

        # Name label
        self._name_label = ctk.CTkLabel(
            self,
            text=scheme.name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self._name_label.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=(6, 4))

        for w in (self, self._name_label):
            w.bind("<Button-1>", lambda e: self._on_click(self))
            w.bind("<Enter>", lambda e: self._on_enter())
            w.bind("<Leave>", lambda e: self._on_leave())

    def _on_enter(self) -> None:
        if not self._selected:
            self.configure(fg_color=BG_HOVER)

    def _on_leave(self) -> None:
        if not self._selected:
            self.configure(fg_color="transparent")

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        if selected:
            self.configure(fg_color=BG_SELECTED)
            self._indicator.configure(fg_color=ACCENT_BLUE)
        else:
            self.configure(fg_color="transparent")
            self._indicator.configure(fg_color="transparent")

    @property
    def scheme(self) -> Scheme:
        return self._scheme

    @property
    def index(self) -> int:
        return self._index


class SchemeListWidget(ctk.CTkScrollableFrame):
    """Scheme list with **fully hidden scrollbar** when content fits.

    Strategy (CTkScrollableFrame deep hack):
      1. Set ``scrollbar_fg_color`` = BG_CARD so the track slot is invisible.
      2. Set ``scrollbar_button_color`` = BG_CARD initially (invisible).
      3. After ``refresh()``, force ``_canvas.update_idletasks()`` then
         measure content vs. visible height.
      4. If content fits → ``pack_forget()`` the scrollbar (removes it from
         layout entirely); the canvas expands to fill the gap.
      5. If content overflows → ``pack()`` it back, tint button to ACCENT_BLUE.
      6. Schedule a second check at +200ms to catch deferred geometry.
    """

    def __init__(self, parent: ctk.CTkBaseClass, **kwargs: Any) -> None:
        super().__init__(
            parent,
            fg_color=BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            # ── scrollbar track invisible (matches BG_CARD) ──────
            scrollbar_fg_color=BG_CARD,
            scrollbar_button_color=BG_CARD,
            scrollbar_button_hover_color=ACCENT_BLUE,
            **kwargs,
        )

        self._scheme_map: dict[int, Scheme] = {}
        self._items: list[_SchemeItem] = []
        self._selected_item: _SchemeItem | None = None

        self.after(100, self._adjust_scrollbar)

    def refresh(self, schemes: list[Scheme]) -> None:
        for item in self._items:
            item.destroy()
        self._items.clear()
        self._scheme_map.clear()
        self._selected_item = None

        for idx, scheme in enumerate(schemes):
            item = _SchemeItem(
                self,
                scheme=scheme,
                index=idx,
                on_click=self._on_item_click,
                fg_color="transparent",
                corner_radius=4,
            )
            item.pack(fill=ctk.X, padx=0, pady=0)
            self._items.append(item)
            self._scheme_map[idx] = scheme

        # Force geometry then check — schedule twice for safety
        self.update_idletasks()
        self._adjust_scrollbar()
        self.after(200, self._adjust_scrollbar)

    def _adjust_scrollbar(self) -> None:
        """Toggle scrollbar visibility by swapping button color.

        ``pack_forget()`` / ``pack()`` is unreliable with CTkScrollbar,
        so we instead set the button (thumb) color to match the track
        when content fits (= invisible), and to ACCENT_BLUE when content
        overflows (= visible).  The track never shows because
        ``scrollbar_fg_color`` is already BG_CARD.
        """
        try:
            self.update_idletasks()
            content_h = len(self._items) * 37  # 36px item + 1px gap
            visible_h = self._parent_canvas.winfo_height()
            if visible_h < 10:
                return

            if content_h <= visible_h + 4:
                # ── Content fits → invisible thumb ───────────────
                self._scrollbar.configure(
                    fg_color=BG_CARD,
                    button_color=BG_CARD,
                    hover_color=BG_CARD,
                )
            else:
                # ── Content overflows → visible thumb ────────────
                self._scrollbar.configure(
                    fg_color=BG_CARD,
                    button_color=ACCENT_BLUE,
                    hover_color=ACCENT_BLUE_HOVER,
                )
        except Exception:
            pass

    def get_selected(self) -> Scheme | None:
        if self._selected_item is not None:
            return self._selected_item.scheme
        return None

    def _on_item_click(self, item: _SchemeItem) -> None:
        if self._selected_item is not None:
            self._selected_item.set_selected(False)
        item.set_selected(True)
        self._selected_item = item
        self.event_generate("<<SchemeSelected>>", when="now")
