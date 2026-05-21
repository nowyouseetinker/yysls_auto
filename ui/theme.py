"""Global UI theme — modern flat design, casual & soft color palette.
Fonts are created lazily to avoid ``RuntimeError`` during test collection.
"""

from __future__ import annotations

import customtkinter as ctk

# ── Color palette ────────────────────────────────────────────────
BG_BASE = "#F0F2F5"       # 主背景（柔和的浅灰）
BG_CARD = "#FFFFFF"        # 卡片/面板背景
BG_HOVER = "#E0E6ED"      # 悬浮态背景（更明显的浅蓝灰）
BG_SELECTED = "#E3F2FD"   # 选中态背景

TEXT_PRIMARY = "#2C3E50"   # 主文字
TEXT_SECONDARY = "#9099A3" # 次要文字（时间戳、辅助信息）
TEXT_ON_COLOR = "#FFFFFF"  # 彩色背景上的文字

ACCENT_BLUE = "#4A90D9"    # 主题蓝色
ACCENT_BLUE_HOVER = "#357ABD"
ACCENT_GREEN = "#4CAF50"   # 启动/成功
ACCENT_GREEN_HOVER = "#388E3C"
ACCENT_RED = "#E74C3C"     # 停止/危险
ACCENT_RED_HOVER = "#C0392B"
ACCENT_ORANGE = "#E67E22"  # 数字/时长高亮

BORDER = "#DFE3E8"         # 分割线/边框
BORDER_FOCUS = "#B0BEC5"   # 输入框焦点边框

# ── Font family ─────────────────────────────────────────────────
FONT_FAMILY = "Microsoft YaHei"

# ── Lazy fonts (created on-demand after root exists) ────────────
_FONTS: dict[str, ctk.CTkFont] = {}

def _font(name: str, size: int = 13, weight: str = "normal") -> ctk.CTkFont:
    key = f"{name}_{size}_{weight}"
    if key not in _FONTS:
        _FONTS[key] = ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)
    return _FONTS[key]

def title_font() -> ctk.CTkFont:
    return _font("title", 15, "bold")

def label_font() -> ctk.CTkFont:
    return _font("label", 14, "bold")

def small_font() -> ctk.CTkFont:
    return _font("small", 13)

def mono_font() -> ctk.CTkFont:
    key = "mono"
    if key not in _FONTS:
        _FONTS[key] = ctk.CTkFont(family="Consolas", size=12)
    return _FONTS[key]

def bold_font() -> ctk.CTkFont:
    return _font("bold", 12, "bold")

# ── CTkFont references for module-level import (deferred) ────────
# These are created lazily. Call after root exists.
# For convenience, we expose getters.
LABEL_FONT = label_font
SMALL_FONT = small_font
MONO_FONT = mono_font
BOLD_FONT = bold_font
TITLE_FONT = title_font

# ── Frame style (reusable kwargs) ────────────────────────────────
FRAME_CARD = {"fg_color": BG_CARD, "corner_radius": 8}
FRAME_BASE = {"fg_color": "transparent", "corner_radius": 0}

# ── Button presets ──────────────────────────────────────────────
BTN_DEFAULT = {
    "fg_color": BG_CARD,
    "text_color": TEXT_PRIMARY,
    "hover_color": BG_HOVER,
    "border_color": BORDER,
    "border_width": 1,
    "corner_radius": 6,
    "height": 28,
}
BTN_PRIMARY = {
    "fg_color": ACCENT_BLUE,
    "text_color": TEXT_ON_COLOR,
    "hover_color": ACCENT_BLUE_HOVER,
    "corner_radius": 6,
    "height": 28,
}
BTN_SUCCESS = {
    "fg_color": ACCENT_GREEN,
    "text_color": TEXT_ON_COLOR,
    "hover_color": ACCENT_GREEN_HOVER,
    "corner_radius": 6,
    "height": 30,
}
BTN_DANGER = {
    "fg_color": ACCENT_RED,
    "text_color": TEXT_ON_COLOR,
    "hover_color": ACCENT_RED_HOVER,
    "corner_radius": 6,
    "height": 30,
}

# ── Helpers ──────────────────────────────────────────────────────

def configure_global() -> None:
    """Call once at app startup to set CTk appearance and theme."""
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
