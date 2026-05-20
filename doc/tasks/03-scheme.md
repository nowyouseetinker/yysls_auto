# 03-scheme — models/scheme.py

**目标文件**: `models/scheme.py` (~65 行)
**预估时间**: 20-30 分钟
**依赖**: 01-enums, 02-action

---

- [ ] **03.1** 声明 `Scheme` 冻结数据类
  _范围_: `models/scheme.py:1-35` | _依赖_: 02 | _测试_: `tests/models/test_scheme.py::test_scheme_creation`
  - 定义 `@dataclass(frozen=True) class Scheme`，字段如下：
    - `id: str`
    - `name: str`
    - `description: str`
    - `actions: tuple[Action, ...]`
    - `loop: bool = True`
    - `start_hotkey: str = "F10"`
    - `stop_hotkey: str = "F12"`
    - `is_preset: bool = False`
  - `__post_init__` 验证：`name` 非空、`actions` 为非空元组、`start_hotkey != stop_hotkey`、非预设方案 `id` 需符合 UUID4 格式
  - 验证冻结不可变性

- [ ] **03.2** 实现 `Scheme.create()` 工厂方法
  _范围_: `models/scheme.py` `create` classmethod | _依赖_: 03.1 | _测试_: `tests/models/test_scheme.py::test_scheme_create_factory`
  - `@classmethod create(cls, name, description, actions, loop=True, start_hotkey="F10", stop_hotkey="F12") -> Scheme`
  - 使用 `uuid.uuid4().hex` 自动生成 `id`
  - 设置 `is_preset=False`
  - 验证每次调用生成唯一 ID

- [ ] **03.3** 实现 `Scheme.create_preset()` 工厂方法
  _范围_: `models/scheme.py` `create_preset` classmethod | _依赖_: 03.2 | _测试_: `tests/models/test_scheme.py::test_scheme_create_preset`
  - `@classmethod create_preset(cls, preset_id, name, description, actions, loop=True, start_hotkey="F10", stop_hotkey="F12") -> Scheme`
  - 使用传入的 `preset_id`（非 UUID），设置 `is_preset=True`
  - 验证返回对象 `is_preset=True`

- [ ] **03.4** 实现 `to_dict()` 和 `from_dict()` 序列化
  _范围_: `models/scheme.py` `to_dict` + `from_dict` | _依赖_: 03.3 | _测试_: `tests/models/test_scheme.py::test_scheme_roundtrip`
  - `to_dict()`：嵌套 actions 通过 `[a.to_dict() for a in self.actions]` 序列化
  - `from_dict(cls, d) -> Scheme`：通过 `Action.from_dict()` 重建 actions，保留所有字段
  - 使用含 5 个 action 的 scheme 进行往返测试
  - 验证 `is_preset` 和 `id` 在序列化中保留

---

**完成标准**: 全部 4 个子任务完成，`pytest tests/models/test_scheme.py` 全部通过。
