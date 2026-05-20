from __future__ import annotations

import sys

from app import create_app
from infra.admin import elevate, is_admin


def main() -> None:
    """Program entry point with admin-privilege check and Tkinter startup."""
    if not is_admin():
        elevate()
        # elevate() calls sys.exit() when not admin — execution never reaches here
        sys.exit(1)

    root = create_app()
    root.mainloop()


if __name__ == "__main__":
    main()
