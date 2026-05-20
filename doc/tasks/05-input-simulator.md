# 05-input-simulator — infra/input_simulator.py

**目标文件**: `infra/input_simulator.py` (~45 行)
**预估时间**: 15-20 分钟
**依赖**: 01-enums（需 ActionType 引用）, pydirectinput

---

- [ ] **05.1** 实现 `press_key()` 函数
  _范围_: `infra/input_simulator.py:1-20` | _依赖_: 01 | _测试_: `tests/infra/test_input_simulator.py::test_press_key_calls_pydirectinput`（mock）
  - `def press_key(key: str, duration: float = 0.1) -> None`
  - 依次调用 `pydirectinput.keyDown(key)`、`time.sleep(duration)`、`pydirectinput.keyUp(key)`
  - 验证 `key` 为非空字符串，`duration >= 0`
  - 测试中 mock `pydirectinput`，验证调用顺序

- [ ] **05.2** 实现 `click_mouse()` 函数
  _范围_: `infra/input_simulator.py:22-35` | _依赖_: 05.1 | _测试_: `tests/infra/test_input_simulator.py::test_click_mouse_calls_pydirectinput`（mock）
  - `def click_mouse(button: str = "left", duration: float = 0.1) -> None`
  - 依次调用 `pydirectinput.mouseDown(button=button)`、`time.sleep(duration)`、`pydirectinput.mouseUp(button=button)`
  - 验证 `button` 为 "left" 或 "right"
  - Mock 测试验证调用顺序

- [ ] **05.3** 实现 `interruptible_sleep()` 函数
  _范围_: `infra/input_simulator.py:37-55` | _依赖_: 05.2 | _测试_: `tests/infra/test_input_simulator.py::test_interruptible_sleep`（使用 threading.Event）
  - `def interruptible_sleep(seconds: float, stop_event: threading.Event) -> bool`
  - 以 0.1 秒为步长睡眠，每次检查 `stop_event.is_set()`
  - 完整睡眠返回 `True`，被中断返回 `False`
  - 验证 `seconds >= 0`
  - 测试：正常睡眠完成返回 True；中途 set event 快速返回 False；零时长立即返回 True

---

**完成标准**: 3 个函数均有 mock 测试通过，interruptible_sleep 行为已验证。
