from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from models.action import Action
from models.scheme import Scheme


class DbRepository:
    """SQLite-based repository for user-defined Scheme persistence.

    Handles CRUD operations for custom schemes stored in a local SQLite database.
    Preset schemes (is_preset=True) are managed by preset_repository and are never
    persisted to or loaded from this database.
    """

    def __init__(self, db_path: str = "macro.db") -> None:
        self._db_path = db_path
        self._init_db()

    # ── 07.1 — database initialization ──────────────────────────

    def _init_db(self) -> None:
        """Open the SQLite connection and ensure the schemes table exists."""
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS schemes (
                id            TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                description   TEXT NOT NULL DEFAULT '',
                actions_json  TEXT NOT NULL,
                loop          INTEGER NOT NULL DEFAULT 1,
                start_hotkey  TEXT NOT NULL DEFAULT 'F10',
                stop_hotkey   TEXT NOT NULL DEFAULT 'F12',
                created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )
        self._conn.commit()

    # ── 07.2 — action serialization helpers ─────────────────────

    def _serialize_actions(self, actions: tuple[Action, ...]) -> str:
        """Encode a tuple of Actions to a JSON string."""
        return json.dumps([a.to_dict() for a in actions], ensure_ascii=False)

    def _deserialize_actions(self, json_str: str) -> tuple[Action, ...]:
        """Decode a JSON string back to a tuple of Actions."""
        data = json.loads(json_str)
        return tuple(Action.from_dict(d) for d in data)

    # ── 07.3 — save ─────────────────────────────────────────────

    def save(self, scheme: Scheme) -> None:
        """Persist a scheme.  Uses INSERT OR REPLACE so re-saving with the same id
        updates the existing row while preserving the original ``created_at``.

        Raises:
            ValueError: If *scheme* is a preset.
        """
        if scheme.is_preset:
            raise ValueError("Cannot save preset schemes to database")

        actions_json = self._serialize_actions(scheme.actions)
        now = datetime.now(UTC).isoformat()

        # Preserve the original creation timestamp when replacing.
        existing = self._conn.execute(
            "SELECT created_at FROM schemes WHERE id = ?", (scheme.id,)
        ).fetchone()
        created_at: str = existing[0] if existing else now

        self._conn.execute(
            """INSERT OR REPLACE INTO schemes
               (id, name, description, actions_json, loop,
                start_hotkey, stop_hotkey, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scheme.id,
                scheme.name,
                scheme.description,
                actions_json,
                int(scheme.loop),
                scheme.start_hotkey,
                scheme.stop_hotkey,
                created_at,
                now,
            ),
        )
        self._conn.commit()

    # ── 07.4 — get_all ──────────────────────────────────────────

    def get_all(self) -> list[Scheme]:
        """Return every user-defined scheme, ordered by creation time."""
        rows = self._conn.execute(
            "SELECT id, name, description, actions_json, loop, "
            "start_hotkey, stop_hotkey "
            "FROM schemes ORDER BY created_at"
        ).fetchall()

        schemes: list[Scheme] = []
        for row in rows:
            actions = self._deserialize_actions(row[3])
            schemes.append(
                Scheme(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    actions=actions,
                    loop=bool(row[4]),
                    start_hotkey=row[5],
                    stop_hotkey=row[6],
                    is_preset=False,
                )
            )
        return schemes

    # ── 07.5 — get_by_id ────────────────────────────────────────

    def get_by_id(self, scheme_id: str) -> Scheme | None:
        """Look up a single scheme by id.  Returns ``None`` when not found."""
        row = self._conn.execute(
            "SELECT id, name, description, actions_json, loop, "
            "start_hotkey, stop_hotkey "
            "FROM schemes WHERE id = ?",
            (scheme_id,),
        ).fetchone()

        if row is None:
            return None

        actions = self._deserialize_actions(row[3])
        return Scheme(
            id=row[0],
            name=row[1],
            description=row[2],
            actions=actions,
            loop=bool(row[4]),
            start_hotkey=row[5],
            stop_hotkey=row[6],
            is_preset=False,
        )

    # ── 07.6 — update / delete ──────────────────────────────────

    def update(self, scheme: Scheme) -> None:
        """Explicitly update an existing scheme in-place.

        Raises:
            ValueError: If *scheme* is a preset.
        """
        if scheme.is_preset:
            raise ValueError("Cannot update preset schemes")

        actions_json = self._serialize_actions(scheme.actions)
        now = datetime.now(UTC).isoformat()

        self._conn.execute(
            """UPDATE schemes
               SET name = ?,
                   description = ?,
                   actions_json = ?,
                   loop = ?,
                   start_hotkey = ?,
                   stop_hotkey = ?,
                   updated_at = ?
               WHERE id = ?""",
            (
                scheme.name,
                scheme.description,
                actions_json,
                int(scheme.loop),
                scheme.start_hotkey,
                scheme.stop_hotkey,
                now,
                scheme.id,
            ),
        )
        self._conn.commit()

    def delete(self, scheme_id: str) -> None:
        """Remove a scheme by id.  No-op when the id does not exist."""
        self._conn.execute("DELETE FROM schemes WHERE id = ?", (scheme_id,))
        self._conn.commit()
