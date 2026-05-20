from __future__ import annotations

import ctypes
import sys


def is_admin() -> bool:
    """Check whether the current process is running with administrator privileges.

    Uses the Windows shell32 API to query the process token.  Returns ``False``
    when the check itself fails (e.g. on a non-Windows platform) so that
    callers can safely fall back to unprivileged mode.
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate() -> None:
    """Re-launch the current process with administrator privileges via UAC.

    If the process is already running as administrator this function is a
    no-op.  Otherwise it calls ``ShellExecuteW`` with the ``"runas"`` verb,
    which triggers a Windows UAC elevation prompt, and then exits the current
    (unelevated) process.

    .. note::

        This function cannot be meaningfully unit-tested because it triggers a
        real UAC prompt and terminates the process.  The body is excluded from
        coverage tracking via ``# pragma: no cover``.
    """
    if is_admin():
        return
    # pragma: no cover
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        " ".join(sys.argv),
        None,
        1,  # SW_SHOWNORMAL
    )
    sys.exit()
