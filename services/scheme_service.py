from __future__ import annotations

from infra import preset_repository
from infra.db_repository import DbRepository
from models.scheme import Scheme


class SchemeService:
    """方案服务：聚合预设方案与自定义方案的 CRUD 操作。

    预设方案只读，不允许修改或删除；
    自定义方案可增删改，数据通过 DbRepository 持久化。
    """

    def __init__(self, db_repo: DbRepository) -> None:
        """注入数据库仓储。

        Args:
            db_repo: 自定义方案的数据库持久化仓储。
        """
        self._db_repo = db_repo

    # ── 11.2 — 验证 ────────────────────────────────────────────

    def _validate_scheme(self, scheme: Scheme) -> None:
        """验证方案字段合法性。

        Args:
            scheme: 待验证的 Scheme 实例。

        Raises:
            ValueError: 任一项验证不通过时抛出，携带具体原因。
        """
        if not scheme.name or not scheme.name.strip():
            raise ValueError("name 不能为空")

        if not scheme.actions:
            raise ValueError("actions 不能为空")

        if not scheme.start_hotkey or not scheme.start_hotkey.strip():
            raise ValueError("start_hotkey 不能为空")

        if not scheme.stop_hotkey or not scheme.stop_hotkey.strip():
            raise ValueError("stop_hotkey 不能为空")

        if scheme.start_hotkey == scheme.stop_hotkey:
            raise ValueError(
                f"start_hotkey 与 stop_hotkey 不能相同: {scheme.start_hotkey!r}"
            )

    # ── 11.3 — 查询 ────────────────────────────────────────────

    def get_all_schemes(self) -> list[Scheme]:
        """返回全部方案：预设在前，自定义在后。

        Returns:
            预设方案列表 + 数据库中的自定义方案列表。
        """
        presets = preset_repository.get_all_presets()
        customs = self._db_repo.get_all()
        return presets + customs

    def get_scheme(self, scheme_id: str) -> Scheme | None:
        """按 ID 查找方案，优先匹配预设方案。

        Args:
            scheme_id: 方案标识符。

        Returns:
            匹配的 Scheme，未找到时返回 None。
        """
        preset = preset_repository.get_preset(scheme_id)
        if preset is not None:
            return preset
        return self._db_repo.get_by_id(scheme_id)

    # ── 11.4 — 创建 ────────────────────────────────────────────

    def create_scheme(self, scheme: Scheme) -> Scheme:
        """验证并保存新自定义方案到数据库。

        Args:
            scheme: 待创建的 Scheme（必须 is_preset=False）。

        Returns:
            已持久化的 Scheme（同传入对象）。

        Raises:
            ValueError: scheme 为预设方案或字段验证不通过。
        """
        if scheme.is_preset:
            raise ValueError("不能创建预设方案（is_preset=True）")
        self._validate_scheme(scheme)
        self._db_repo.save(scheme)
        return scheme

    # ── 11.5 — 更新 / 删除 ────────────────────────────────────

    def update_scheme(self, scheme: Scheme) -> Scheme:
        """更新已有自定义方案。禁止修改预设方案。

        Args:
            scheme: 包含更新后字段的 Scheme（必须 is_preset=False）。

        Returns:
            更新后的 Scheme。

        Raises:
            ValueError: scheme 为预设方案或字段验证不通过。
        """
        if scheme.is_preset:
            raise ValueError("不能修改预设方案")
        self._validate_scheme(scheme)
        self._db_repo.update(scheme)
        return scheme

    def delete_scheme(self, scheme_id: str) -> None:
        """删除自定义方案。禁止删除预设方案。

        Args:
            scheme_id: 待删除的方案 ID。

        Raises:
            ValueError: scheme_id 属于预设方案。
        """
        if preset_repository.get_preset(scheme_id) is not None:
            raise ValueError(f"不能删除预设方案: {scheme_id}")
        self._db_repo.delete(scheme_id)
