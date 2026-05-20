# 07-db-repository — infra/db_repository.py

**目标文件**: `infra/db_repository.py` (~130 行)
**预估时间**: 30-40 分钟
**依赖**: 01-enums, 02-action, 03-scheme（数据模型）, sqlite3

---

- [ ] **07.1** 实现 `__init__` 和 `_init_db()`
  _范围_: `infra/db_repository.py:1-40` | _依赖_: 02, 03 | _测试_: `tests/infra/test_db_repository.py::test_init_db_creates_table`
  - `class DbRepository`：`__init__(self, db_path: str = "macro.db")` 存储路径，调用 `_init_db()`
  - `_init_db()`：连接，`CREATE TABLE IF NOT EXISTS schemes (...)`（按设计文档 schema），提交，关闭
  - 使用 `sqlite3.connect()` + `check_same_thread=False` 支持跨线程访问
  - 测试：创建内存数据库（`:memory:` 或 tmpfile），通过 `PRAGMA table_info` 验证表存在

- [ ] **07.2** 实现 `_serialize_actions()` 和 `_deserialize_actions()`
  _范围_: `infra/db_repository.py:42-65` | _依赖_: 07.1 | _测试_: `tests/infra/test_db_repository.py::test_serialize_actions_roundtrip`
  - `_serialize_actions(actions: tuple[Action, ...]) -> str`：`json.dumps([a.to_dict() for a in actions], ensure_ascii=False)`
  - `_deserialize_actions(json_str: str) -> tuple[Action, ...]`：解析 JSON，`tuple(Action.from_dict(d) for d in data)`
  - 测试：3 个 action（每种类型一个）的往返序列化

- [ ] **07.3** 实现 `save()` 方法
  _范围_: `infra/db_repository.py:67-85` | _依赖_: 07.2 | _测试_: `tests/infra/test_db_repository.py::test_save_and_get_by_id`
  - `def save(self, scheme: Scheme) -> str`：INSERT INTO schemes，`actions_json` 来自 `_serialize_actions`
  - 返回 scheme id
  - 若 id 已存在抛出 `ValueError`（UNIQUE 约束）
  - 测试：保存 Scheme，再取出，验证所有字段一致

- [ ] **07.4** 实现 `get_all()` 方法
  _范围_: `infra/db_repository.py:87-100` | _依赖_: 07.3 | _测试_: `tests/infra/test_db_repository.py::test_get_all`
  - `def get_all(self) -> list[Scheme]`：SELECT * FROM schemes ORDER BY created_at
  - 返回通过 `from_dict()` 重建的 Scheme 对象列表
  - 测试：保存 2 个 scheme，get_all 返回两者

- [ ] **07.5** 实现 `get_by_id()` 方法
  _范围_: `infra/db_repository.py:102-115` | _依赖_: 07.3 | _测试_: `tests/infra/test_db_repository.py::test_get_by_id_not_found`
  - `def get_by_id(self, id: str) -> Scheme | None`
  - 未找到行时返回 None
  - 测试：保存 scheme，按 id 取出；查询不存在的 id 返回 None

- [ ] **07.6** 实现 `update()` 和 `delete()` 方法
  _范围_: `infra/db_repository.py:117-150` | _依赖_: 07.5 | _测试_: `tests/infra/test_db_repository.py::test_update`, `test_delete`
  - `def update(self, scheme: Scheme) -> None`：UPDATE schemes SET ... WHERE id=?，更新 `updated_at = datetime.now()`
  - `def delete(self, id: str) -> None`：DELETE FROM schemes WHERE id=?
  - 测试：保存后更新名称，get_by_id 返回更新后名称和 changed updated_at
  - 测试：保存后删除，get_by_id 返回 None

---

**完成标准**: 全部 6 个子任务完成，CRUD 测试在内存 SQLite 上通过。
