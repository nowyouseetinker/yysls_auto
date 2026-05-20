from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from infra.db_repository import DbRepository
from models.action import Action
from models.scheme import Scheme
from services.scheme_service import SchemeService

# ── helpers ─────────────────────────────────────────────────────────


def _mutate(obj: Scheme, **kwargs: object) -> Scheme:
    """Bypass frozen-dataclass protection to mutate fields in-place.

    Used only in tests to construct intentionally-invalid Scheme objects
    that would otherwise be rejected by ``__post_init__``.
    """
    for key, value in kwargs.items():
        object.__setattr__(obj, key, value)
    return obj


# ── fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def mock_db() -> MagicMock:
    """Return a MagicMock wrapping DbRepository."""
    return MagicMock(spec=DbRepository)


@pytest.fixture
def service(mock_db: MagicMock) -> SchemeService:
    """Return a SchemeService with mocked DbRepository."""
    return SchemeService(db_repo=mock_db)


@pytest.fixture
def sample_actions() -> tuple[Action, ...]:
    """Return a minimal valid actions tuple for tests."""
    return (Action.key_press("F", order=0),)


@pytest.fixture
def custom_scheme(sample_actions: tuple[Action, ...]) -> Scheme:
    """Return a valid custom Scheme (not a preset)."""
    return Scheme.create(
        name="测试方案",
        description="用于测试的自定义方案",
        actions=sample_actions,
    )


@pytest.fixture
def preset_scheme(sample_actions: tuple[Action, ...]) -> Scheme:
    """Return a preset Scheme for rejection tests."""
    return Scheme.create_preset(
        preset_id="preset_test_x",
        name="测试预设",
        description="用于测试的预设方案",
        actions=sample_actions,
    )


# ── 11.1 — init ────────────────────────────────────────────────────


class TestInit:
    def test_init_stores_db_repo(self, mock_db: MagicMock) -> None:
        service = SchemeService(db_repo=mock_db)
        assert service._db_repo is mock_db


# ── 11.2 — _validate_scheme ────────────────────────────────────────


class TestValidateScheme:
    def test_validate_accepts_valid_custom(
        self, service: SchemeService, custom_scheme: Scheme
    ) -> None:
        # Should not raise
        service._validate_scheme(custom_scheme)

    def test_validate_rejects_empty_name(
        self, service: SchemeService, custom_scheme: Scheme
    ) -> None:
        scheme = _mutate(custom_scheme, name="")
        with pytest.raises(ValueError, match="name 不能为空"):
            service._validate_scheme(scheme)

    def test_validate_rejects_whitespace_name(
        self, service: SchemeService, custom_scheme: Scheme
    ) -> None:
        scheme = _mutate(custom_scheme, name="   ")
        with pytest.raises(ValueError, match="name 不能为空"):
            service._validate_scheme(scheme)

    def test_validate_rejects_empty_actions(
        self, service: SchemeService, custom_scheme: Scheme
    ) -> None:
        scheme = _mutate(custom_scheme, actions=())
        with pytest.raises(ValueError, match="actions 不能为空"):
            service._validate_scheme(scheme)

    def test_validate_rejects_empty_start_hotkey(
        self, service: SchemeService, sample_actions: tuple[Action, ...]
    ) -> None:
        scheme = Scheme(
            id="aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
            name="x",
            description="",
            actions=sample_actions,
            start_hotkey="",
        )
        with pytest.raises(ValueError, match="start_hotkey 不能为空"):
            service._validate_scheme(scheme)

    def test_validate_rejects_empty_stop_hotkey(
        self, service: SchemeService, sample_actions: tuple[Action, ...]
    ) -> None:
        scheme = Scheme(
            id="aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa",
            name="x",
            description="",
            actions=sample_actions,
            stop_hotkey="",
        )
        with pytest.raises(ValueError, match="stop_hotkey 不能为空"):
            service._validate_scheme(scheme)

    def test_validate_rejects_same_hotkeys(
        self, service: SchemeService, custom_scheme: Scheme
    ) -> None:
        scheme = _mutate(custom_scheme, start_hotkey="F10", stop_hotkey="F10")
        with pytest.raises(ValueError, match="不能相同"):
            service._validate_scheme(scheme)


# ── 11.3 — get_all_schemes / get_scheme ────────────────────────────


class TestGetAllSchemes:
    def test_get_all_merges_presets_and_custom(
        self, service: SchemeService, mock_db: MagicMock, custom_scheme: Scheme
    ) -> None:
        mock_db.get_all.return_value = [custom_scheme]
        result = service.get_all_schemes()

        # 4 presets + 1 custom = 5
        assert len(result) >= 5
        # Presets come first
        assert result[0].is_preset is True
        assert result[1].is_preset is True
        assert result[2].is_preset is True
        assert result[3].is_preset is True
        # Custom at the end
        assert result[-1] is custom_scheme

    def test_get_all_no_customs(
        self, service: SchemeService, mock_db: MagicMock
    ) -> None:
        mock_db.get_all.return_value = []
        result = service.get_all_schemes()
        # Only presets (4)
        assert len(result) == 4
        assert all(s.is_preset for s in result)


class TestGetScheme:
    def test_get_scheme_finds_preset(self, service: SchemeService) -> None:
        scheme = service.get_scheme("preset_zha_yu")
        assert scheme is not None
        assert scheme.id == "preset_zha_yu"
        assert scheme.is_preset is True

    def test_get_scheme_falls_back_to_db(
        self, service: SchemeService, mock_db: MagicMock, custom_scheme: Scheme
    ) -> None:
        mock_db.get_by_id.return_value = custom_scheme
        scheme = service.get_scheme("nonexistent_preset_id")
        mock_db.get_by_id.assert_called_once_with("nonexistent_preset_id")
        assert scheme is custom_scheme

    def test_get_scheme_not_found(
        self, service: SchemeService, mock_db: MagicMock
    ) -> None:
        mock_db.get_by_id.return_value = None
        scheme = service.get_scheme("no_such_id")
        assert scheme is None
        mock_db.get_by_id.assert_called_once_with("no_such_id")


# ── 11.4 — create_scheme ───────────────────────────────────────────


class TestCreateScheme:
    def test_create_scheme_saves_to_db(
        self, service: SchemeService, mock_db: MagicMock, custom_scheme: Scheme
    ) -> None:
        result = service.create_scheme(custom_scheme)
        mock_db.save.assert_called_once_with(custom_scheme)
        assert result is custom_scheme

    def test_create_scheme_rejects_preset(
        self, service: SchemeService, preset_scheme: Scheme
    ) -> None:
        with pytest.raises(ValueError, match="不能创建预设方案"):
            service.create_scheme(preset_scheme)

    def test_create_scheme_rejects_invalid(
        self, service: SchemeService, custom_scheme: Scheme
    ) -> None:
        scheme = _mutate(custom_scheme, name="  ")
        with pytest.raises(ValueError):
            service.create_scheme(scheme)


# ── 11.5 — update_scheme / delete_scheme ───────────────────────────


class TestUpdateScheme:
    def test_update_scheme_calls_db_update(
        self, service: SchemeService, mock_db: MagicMock, custom_scheme: Scheme
    ) -> None:
        result = service.update_scheme(custom_scheme)
        mock_db.update.assert_called_once_with(custom_scheme)
        assert result is custom_scheme

    def test_update_scheme_rejects_preset(
        self, service: SchemeService, preset_scheme: Scheme
    ) -> None:
        with pytest.raises(ValueError, match="不能修改预设方案"):
            service.update_scheme(preset_scheme)

    def test_update_scheme_rejects_invalid(
        self, service: SchemeService, custom_scheme: Scheme
    ) -> None:
        scheme = _mutate(custom_scheme, actions=())
        with pytest.raises(ValueError, match="actions 不能为空"):
            service.update_scheme(scheme)


class TestDeleteScheme:
    def test_delete_scheme_calls_db_delete(
        self, service: SchemeService, mock_db: MagicMock, custom_scheme: Scheme
    ) -> None:
        service.delete_scheme(custom_scheme.id)
        mock_db.delete.assert_called_once_with(custom_scheme.id)

    def test_cannot_delete_preset(self, service: SchemeService) -> None:
        with pytest.raises(ValueError, match="不能删除预设方案"):
            service.delete_scheme("preset_zha_yu")

    def test_delete_nonexistent_is_noop(
        self, service: SchemeService, mock_db: MagicMock
    ) -> None:
        # A non-preset, non-existent ID should just pass through to DB
        service.delete_scheme("nonexistent_uuid_12345")
        mock_db.delete.assert_called_once_with("nonexistent_uuid_12345")
