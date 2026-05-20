# 06-keyboard-hook — infra/keyboard_hook.py

**目标文件**: `infra/keyboard_hook.py` (~45 行)
**预估时间**: 15-20 分钟
**依赖**: 无（叶子模块，仅 keyboard 库）

---

- [ ] **06.1** 实现 `register_hotkey()` 函数
  _范围_: `infra/keyboard_hook.py:1-25` | _依赖_: 无 | _测试_: `tests/infra/test_keyboard_hook.py::test_register_hotkey_calls_keyboard`（mock）
  - `def register_hotkey(key: str, callback: Callable[[], None]) -> None`
  - 封装 `keyboard.add_hotkey(key, callback)`
  - 验证 `key` 为非空字符串，`callback` 为可调用对象
  - 测试中 mock `keyboard.add_hotkey`，验证参数正确传递

- [ ] **06.2** 实现 `unregister_hotkey()` 函数
  _范围_: `infra/keyboard_hook.py:27-40` | _依赖_: 06.1 | _测试_: `tests/infra/test_keyboard_hook.py::test_unregister_hotkey_calls_keyboard`（mock）
  - `def unregister_hotkey(key: str) -> None`
  - 封装 `keyboard.remove_hotkey(key)`，若 hook 存在则移除
  - 优雅处理未注册的 hook（捕获异常，无操作，不崩溃）

- [ ] **06.3** 实现 `clear_all()` 函数
  _范围_: `infra/keyboard_hook.py:42-55` | _依赖_: 06.2 | _测试_: `tests/infra/test_keyboard_hook.py::test_clear_all_calls_keyboard`（mock）
  - `def clear_all() -> None`
  - 封装 `keyboard.unhook_all_hotkeys()` 或 `keyboard.clear_all_hotkeys()`
  - 测试验证调用了正确的底层函数

---

**完成标准**: 3 个封装函数均有 mock 测试通过。
