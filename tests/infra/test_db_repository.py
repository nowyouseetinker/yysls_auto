from __future__ import annotations

import pytest

from infra.db_repository import DbRepository
from models.action import Action
from models.enums import MouseButton
from models.scheme import Scheme


def _make_sample_actions(count: int = 3) -> tuple[Action, ...]:
    """Build a small tuple of key-press actions for tests."""
    actions: list[Action] = []
    for i in range(count):
        actions.append(Action.key_press(f"F{i+1}", order=i))
    return tuple(actions)


def _make_scheme(name: str = "测试方案") -> Scheme:
    """Create a minimal user-defined Scheme via the create() factory."""
    return Scheme.create(
        name=name,
        description="",
        actions=_make_sample_actions(2),
    )


def _make_preset() -> Scheme:
    """Create a preset Scheme for rejection tests."""
    return Scheme.create_preset(
        preset_id="preset_test",
        name="预设方案",
        description="",
        actions=_make_sample_actions(1),
    )


# ═══════════════════════════════════════════════════════════════
# 07.1 — _init_db creates the schemes table
# ═══════════════════════════════════════════════════════════════


class TestInitDb:
    """Verify the database connection and table creation."""

    def test_init_db_creates_table(self) -> None:
        repo = DbRepository(db_path=":memory:")
        rows = repo._conn.execute("PRAGMA table_info('schemes')").fetchall()
        columns = {row[1] for row in rows}
        expected = {
            "id",
            "name",
            "description",
            "actions_json",
            "loop",
            "start_hotkey",
            "stop_hotkey",
            "created_at",
            "updated_at",
        }
        assert columns == expected

    def test_init_db_id_is_primary_key(self) -> None:
        repo = DbRepository(db_path=":memory:")
        rows = repo._conn.execute("PRAGMA table_info('schemes')").fetchall()
        id_row = next(r for r in rows if r[1] == "id")
        # pk column is index 5 in PRAGMA table_info output
        assert id_row[5] == 1

    def test_table_is_empty_on_creation(self) -> None:
        repo = DbRepository(db_path=":memory:")
        count = repo._conn.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
        assert count == 0


# ═══════════════════════════════════════════════════════════════
# 07.2 — action serialization roundtrip
# ═══════════════════════════════════════════════════════════════


class TestActionSerialization:
    """Verify _serialize_actions / _deserialize_actions roundtrip."""

    def test_serialize_actions_roundtrip_all_types(self) -> None:
        repo = DbRepository(db_path=":memory:")
        actions: tuple[Action, ...] = (
            Action.key_press("Space", order=0, duration=0.1),
            Action.mouse_click(MouseButton.LEFT, order=1, duration=0.05),
            Action.wait_fixed(5.0, order=2),
            Action.wait_random(10.0, 12.0, order=3),
        )
        json_str = repo._serialize_actions(actions)
        restored = repo._deserialize_actions(json_str)
        assert len(restored) == 4
        for orig, rest in zip(actions, restored, strict=True):
            assert rest == orig, f"Action mismatch: {orig!r} vs {rest!r}"

    def test_serialize_single_action(self) -> None:
        repo = DbRepository(db_path=":memory:")
        action = Action.key_press("F", order=0)
        json_str = repo._serialize_actions((action,))
        restored = repo._deserialize_actions(json_str)
        assert len(restored) == 1
        assert restored[0] == action

    def test_serialize_empty_tuple(self) -> None:
        repo = DbRepository(db_path=":memory:")
        json_str = repo._serialize_actions(())
        assert json_str == "[]"
        restored = repo._deserialize_actions(json_str)
        assert restored == ()


# ═══════════════════════════════════════════════════════════════
# 07.3 — save + get_by_id
# ═══════════════════════════════════════════════════════════════


class TestSaveAndGetById:
    """Verify save() persists a scheme and get_by_id() retrieves it."""

    def test_save_and_get_by_id_all_fields_match(self) -> None:
        repo = DbRepository(db_path=":memory:")
        scheme = _make_scheme("完整校验")
        repo.save(scheme)

        retrieved = repo.get_by_id(scheme.id)
        assert retrieved is not None
        assert retrieved.id == scheme.id
        assert retrieved.name == scheme.name
        assert retrieved.description == scheme.description
        assert len(retrieved.actions) == len(scheme.actions)
        for ra, sa in zip(retrieved.actions, scheme.actions, strict=True):
            assert ra == sa
        assert retrieved.loop == scheme.loop
        assert retrieved.start_hotkey == scheme.start_hotkey
        assert retrieved.stop_hotkey == scheme.stop_hotkey
        assert retrieved.is_preset is False

    def test_save_persists_is_preset_false(self) -> None:
        """Saved schemes always come back as non-preset."""
        repo = DbRepository(db_path=":memory:")
        scheme = _make_scheme("标记测试")
        repo.save(scheme)
        retrieved = repo.get_by_id(scheme.id)
        assert retrieved is not None
        assert retrieved.is_preset is False

    def test_save_insert_or_replace_preserves_created_at(self) -> None:
        repo = DbRepository(db_path=":memory:")
        scheme = _make_scheme("重复保存")
        repo.save(scheme)

        row_before = repo._conn.execute(
            "SELECT created_at FROM schemes WHERE id = ?", (scheme.id,)
        ).fetchone()
        assert row_before is not None

        # Re-save with the same id (INSERT OR REPLACE).
        repo.save(scheme)
        row_after = repo._conn.execute(
            "SELECT created_at FROM schemes WHERE id = ?", (scheme.id,)
        ).fetchone()
        assert row_after is not None
        assert row_after[0] == row_before[0]


# ═══════════════════════════════════════════════════════════════
# 07.4 — get_all
# ═══════════════════════════════════════════════════════════════


class TestGetAll:
    """Verify get_all() returns all stored schemes."""

    def test_get_all_returns_all_saved_schemes(self) -> None:
        repo = DbRepository(db_path=":memory:")
        s1 = _make_scheme("方案A")
        s2 = _make_scheme("方案B")
        repo.save(s1)
        repo.save(s2)

        all_schemes = repo.get_all()
        assert len(all_schemes) == 2
        ids = {s.id for s in all_schemes}
        assert s1.id in ids
        assert s2.id in ids

    def test_get_all_empty_when_no_schemes(self) -> None:
        repo = DbRepository(db_path=":memory:")
        assert repo.get_all() == []

    def test_get_all_excludes_presets(self) -> None:
        """Presets should never appear in get_all() because they are not saved to DB."""
        repo = DbRepository(db_path=":memory:")
        s = _make_scheme("普通方案")
        repo.save(s)
        all_schemes = repo.get_all()
        assert all(s.is_preset is False for s in all_schemes)

    def test_get_all_ordered_by_created_at(self) -> None:
        repo = DbRepository(db_path=":memory:")
        s1 = _make_scheme("先保存")
        s2 = _make_scheme("后保存")
        repo.save(s1)
        repo.save(s2)

        all_schemes = repo.get_all()
        assert len(all_schemes) == 2
        # s1 was saved first and should appear before s2
        assert all_schemes[0].id == s1.id
        assert all_schemes[1].id == s2.id


# ═══════════════════════════════════════════════════════════════
# 07.5 — get_by_id negative cases
# ═══════════════════════════════════════════════════════════════


class TestGetByIdEdgeCases:
    """Verify get_by_id() handles missing ids correctly."""

    def test_get_by_id_not_found_returns_none(self) -> None:
        repo = DbRepository(db_path=":memory:")
        result = repo.get_by_id("nonexistent-id")
        assert result is None

    def test_get_by_id_after_delete_returns_none(self) -> None:
        repo = DbRepository(db_path=":memory:")
        scheme = _make_scheme()
        repo.save(scheme)
        repo.delete(scheme.id)
        assert repo.get_by_id(scheme.id) is None

    def test_get_by_id_empty_string_returns_none(self) -> None:
        repo = DbRepository(db_path=":memory:")
        assert repo.get_by_id("") is None


# ═══════════════════════════════════════════════════════════════
# 07.6 — update / delete
# ═══════════════════════════════════════════════════════════════


class TestUpdate:
    """Verify update() modifies an existing scheme."""

    def test_update_changes_name(self) -> None:
        repo = DbRepository(db_path=":memory:")
        scheme = _make_scheme("原始名称")
        repo.save(scheme)

        updated = Scheme(
            id=scheme.id,
            name="新名称",
            description="更新后的描述",
            actions=scheme.actions,
            loop=False,
            start_hotkey="F5",
            stop_hotkey="F6",
            is_preset=False,
        )
        repo.update(updated)

        retrieved = repo.get_by_id(scheme.id)
        assert retrieved is not None
        assert retrieved.name == "新名称"
        assert retrieved.description == "更新后的描述"
        assert retrieved.loop is False
        assert retrieved.start_hotkey == "F5"
        assert retrieved.stop_hotkey == "F6"

    def test_update_changes_updated_at(self) -> None:
        repo = DbRepository(db_path=":memory:")
        scheme = _make_scheme()
        repo.save(scheme)

        row_before = repo._conn.execute(
            "SELECT updated_at FROM schemes WHERE id = ?", (scheme.id,)
        ).fetchone()
        assert row_before is not None

        repo.update(scheme)

        row_after = repo._conn.execute(
            "SELECT updated_at FROM schemes WHERE id = ?", (scheme.id,)
        ).fetchone()
        assert row_after is not None
        # updated_at should change after update
        assert row_after[0] != row_before[0]

    def test_update_preserves_created_at(self) -> None:
        repo = DbRepository(db_path=":memory:")
        scheme = _make_scheme()
        repo.save(scheme)

        row_before = repo._conn.execute(
            "SELECT created_at FROM schemes WHERE id = ?", (scheme.id,)
        ).fetchone()
        assert row_before is not None

        updated = Scheme(
            id=scheme.id,
            name="新名称",
            description="",
            actions=scheme.actions,
            is_preset=False,
        )
        repo.update(updated)

        row_after = repo._conn.execute(
            "SELECT created_at FROM schemes WHERE id = ?", (scheme.id,)
        ).fetchone()
        assert row_after is not None
        assert row_after[0] == row_before[0]


class TestDelete:
    """Verify delete() removes a scheme."""

    def test_delete_removes_scheme(self) -> None:
        repo = DbRepository(db_path=":memory:")
        scheme = _make_scheme()
        repo.save(scheme)
        repo.delete(scheme.id)
        assert repo.get_by_id(scheme.id) is None

    def test_delete_nonexistent_is_noop(self) -> None:
        repo = DbRepository(db_path=":memory:")
        # Should not raise
        repo.delete("does-not-exist")

    def test_delete_only_removes_target(self) -> None:
        repo = DbRepository(db_path=":memory:")
        s1 = _make_scheme("保留")
        s2 = _make_scheme("删除")
        repo.save(s1)
        repo.save(s2)
        repo.delete(s2.id)

        all_remaining = repo.get_all()
        assert len(all_remaining) == 1
        assert all_remaining[0].id == s1.id


# ═══════════════════════════════════════════════════════════════
# Preset rejection
# ═══════════════════════════════════════════════════════════════


class TestPresetRejection:
    """Verify that preset schemes are refused by save and update."""

    def test_save_preset_raises_value_error(self) -> None:
        repo = DbRepository(db_path=":memory:")
        preset = _make_preset()
        with pytest.raises(ValueError, match="preset"):
            repo.save(preset)

    def test_update_preset_raises_value_error(self) -> None:
        repo = DbRepository(db_path=":memory:")
        preset = _make_preset()
        with pytest.raises(ValueError, match="preset"):
            repo.update(preset)
