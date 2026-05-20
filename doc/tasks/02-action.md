# 02-action — models/action.py

**目标文件**: `models/action.py` (~85 行)
**预估时间**: 25-35 分钟
**依赖**: 01-enums

---

- [ ] **02.1** 声明 `Action` 冻结数据类
  _范围_: `models/action.py:1-40` | _依赖_: 01 | _测试_: `tests/models/test_action.py::test_action_creation`
  - 定义 `@dataclass(frozen=True) class Action`，字段如下：
    - `action_type: ActionType`
    - `order: int`
    - `key: str | None = None`
    - `mouse_button: MouseButton | None = None`
    - `duration: float = 0.1`
    - `wait_seconds: float | None = None`
    - `wait_min: float | None = None`
    - `wait_max: float | None = None`
  - 验证 `frozen=True` 阻止属性修改（尝试 `action.order = 999` 抛出 `FrozenInstanceError`）

- [ ] **02.2** 实现 `__post_init__` 验证
  _范围_: `models/action.py` `__post_init__` 方法 | _依赖_: 02.1 | _测试_: `tests/models/test_action.py::test_action_validation`
  - KEY_PRESS 要求 `key` 非 None，`mouse_button` 为 None
  - MOUSE_CLICK 要求 `mouse_button` 非 None，`key` 为 None
  - WAIT 要求 `wait_seconds` 非 None 或 `wait_min` 和 `wait_max` 同时非 None（二选一，不能同时存在）
  - WAIT 要求 `key` 和 `mouse_button` 均为 None
  - 所有类型：`order >= 0`，`duration >= 0`
  - 违反时抛出 `ValueError` 并附描述性消息

- [ ] **02.3** 实现 `Action.key_press()` 工厂方法
  _范围_: `models/action.py` `key_press` classmethod | _依赖_: 02.2 | _测试_: `tests/models/test_action.py::test_key_press_factory`
  - `@classmethod key_press(cls, key: str, order: int, duration: float = 0.1) -> Action`
  - 返回 `Action(action_type=ActionType.KEY_PRESS, key=key, order=order, duration=duration)`
  - 验证返回的 Action 通过验证

- [ ] **02.4** 实现 `Action.mouse_click()` 和 `Action.wait_fixed()` 工厂方法
  _范围_: `models/action.py` `mouse_click` 和 `wait_fixed` classmethod | _依赖_: 02.3 | _测试_: `tests/models/test_action.py::test_mouse_click_factory`, `test_wait_fixed_factory`
  - `mouse_click(cls, button: MouseButton, order: int, duration: float = 0.1) -> Action`
  - `wait_fixed(cls, seconds: float, order: int) -> Action`：设置 `wait_seconds=seconds`，其余可选字段为 None
  - 两者均返回合法的 Action 对象

- [ ] **02.5** 实现 `Action.wait_random()` 工厂方法和 `__str__()`
  _范围_: `models/action.py` `wait_random` classmethod + `__str__` | _依赖_: 02.4 | _测试_: `tests/models/test_action.py::test_wait_random_factory`, `test_action_str`
  - `wait_random(cls, min_s: float, max_s: float, order: int) -> Action`：设置 `wait_min`、`wait_max`，若 `min_s > max_s` 抛出 ValueError
  - `__str__` 返回需求文档中的中文描述（如 `"按键 Space (0.1s)"`、`"鼠标左键点击 (0.1s)"`、`"等待 95~105 秒"`、`"等待 5 秒"`）
  - 验证三种操作类型均生成可读的中文字符串

- [ ] **02.6** 实现 `to_dict()` 和 `from_dict()` 序列化
  _范围_: `models/action.py` `to_dict` 方法 + `from_dict` classmethod | _依赖_: 02.5 | _测试_: `tests/models/test_action.py::test_action_roundtrip`
  - `to_dict()` 返回适合 `json.dumps` 的字典（枚举转字符串，保留 None）
  - `from_dict(cls, d: dict) -> Action` 重建 Action，往返保持相等
  - 测试四种工厂类型的往返序列化

---

**完成标准**: 全部 6 个子任务完成，`pytest tests/models/test_action.py` 全部通过。
