# 01-enums — models/enums.py

**目标文件**: `models/enums.py` (~15 行)
**预估时间**: 8-10 分钟
**依赖**: 无（叶子模块）

---

- [ ] **01.1** 定义 `ActionType` 枚举
  _范围_: `models/enums.py:1-12` | _依赖_: 无 | _测试_: `tests/models/test_enums.py::test_action_type_values`
  - 定义 `class ActionType(str, Enum)` 包含 3 个成员：
    - `KEY_PRESS = "key_press"`
    - `MOUSE_CLICK = "mouse_click"`
    - `WAIT = "wait"`
  - 验证 `list(ActionType)` 返回 3 个成员
  - 验证每个成员的 `.value` 是小写下划线格式字符串

- [ ] **01.2** 定义 `MouseButton` 枚举
  _范围_: `models/enums.py:14-22` | _依赖_: 01.1 | _测试_: `tests/models/test_enums.py::test_mouse_button_values`
  - 定义 `class MouseButton(str, Enum)` 包含 2 个成员：
    - `LEFT = "left"`
    - `RIGHT = "right"`
  - 验证 `list(MouseButton)` 返回 2 个成员

---

**完成标准**: 两个枚举均可导入，测试通过，共 3+2 个枚举成员已验证。
