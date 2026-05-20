# 11-scheme-service — services/scheme_service.py

**目标文件**: `services/scheme_service.py` (~110 行)
**预估时间**: 25-35 分钟
**依赖**: 07-db-repository, 08-preset-repository, 01-03 models

---

- [ ] **11.1** 实现 `SchemeService.__init__` 和依赖注入
  _范围_: `services/scheme_service.py:1-20` | _依赖_: 07, 08 | _测试_: `tests/services/test_scheme_service.py::test_init`
  - `class SchemeService`：接收 `db_repo: DbRepository` 和 `preset_repo` 模块
  - 存储为实例属性

- [ ] **11.2** 实现 `_validate_scheme()` 私有方法
  _范围_: `services/scheme_service.py:22-45` | _依赖_: 11.1 | _测试_: `tests/services/test_scheme_service.py::test_validate_rejects_empty_actions`
  - 验证：name 非空、actions 非空、start_hotkey 非空、stop_hotkey 非空、start != stop
  - 每种违反情况抛出 `ValueError` 并附具体消息
  - 测试每种验证情况

- [ ] **11.3** 实现 `get_all_schemes()` 和 `get_scheme()`
  _范围_: `services/scheme_service.py:47-70` | _依赖_: 11.2 | _测试_: `tests/services/test_scheme_service.py::test_get_all_merges_presets_and_custom`
  - `get_all_schemes()`：返回 `presets + db_repo.get_all()`，presets 在前
  - `get_scheme(id)`：先查 presets，再查 DB；未找到返回 None
  - 测试：mock db 返回 1 个 scheme，get_all 返回 4 presets + 1 custom = 5

- [ ] **11.4** 实现 `create_scheme()`
  _范围_: `services/scheme_service.py:72-90` | _依赖_: 11.3 | _测试_: `tests/services/test_scheme_service.py::test_create_scheme`
  - `create_scheme(scheme: Scheme) -> Scheme`：验证，然后 `db_repo.save(scheme)`，返回 scheme
  - 禁止创建 is_preset=True 的 scheme（抛出 ValueError）
  - 测试：创建合法 scheme，验证 db.save 被调用

- [ ] **11.5** 实现 `update_scheme()` 和 `delete_scheme()`
  _范围_: `services/scheme_service.py:92-120` | _依赖_: 11.4 | _测试_: `tests/services/test_scheme_service.py::test_cannot_delete_preset`
  - `update_scheme(scheme: Scheme) -> Scheme`：验证，拒绝 is_preset（预设保护），调用 `db_repo.update(scheme)`
  - `delete_scheme(id: str) -> None`：检查 id 是否属于预设（抛出 ValueError），否则调用 `db_repo.delete(id)`
  - 测试：尝试删除/更新预设方案抛出 ValueError

---

**完成标准**: CRUD 编排正确，预设方案修改保护通过测试。
