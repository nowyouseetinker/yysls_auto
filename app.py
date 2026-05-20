from __future__ import annotations

import tkinter as tk

from infra import input_simulator, keyboard_hook
from infra.db_repository import DbRepository
from services.hotkey_service import HotkeyService
from services.log_service import LogService
from services.macro_engine import MacroEngine
from services.scheme_service import SchemeService
from ui.main_window import MainWindow


def create_app(db_path: str = "schemes.db") -> tk.Tk:
    """Assemble all dependencies and return the configured Tk root.

    Instantiates every layer in dependency order:
        LogService -> DbRepository -> MacroEngine -> SchemeService ->
        HotkeyService -> MainWindow (with root Tk).

    Args:
        db_path: Path passed to :class:`DbRepository`.  Use ``":memory:"``
            for an in-memory database (e.g. during tests).

    Returns:
        The :class:`tk.Tk` root window, fully wired with all services and
        widgets.
    """
    log_service = LogService()
    db_repo = DbRepository(db_path)
    macro_engine = MacroEngine(log_service, input_simulator)
    scheme_service = SchemeService(db_repo)
    hotkey_service = HotkeyService(keyboard_hook, macro_engine, log_service)

    root = tk.Tk()
    _ = MainWindow(root, scheme_service, hotkey_service, macro_engine, log_service)
    return root
