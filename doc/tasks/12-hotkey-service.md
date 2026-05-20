# 12-hotkey-service — services/hotkey_service.py

**目标文件**: `services/hotkey_service.py` (~70 行)
**预估时间**: 20-25 分钟
**依赖**: 06-keyboard-hook, 09-log-service, 10-macro-engine, 01-03 models

---

- [ ] **12.1** 实现 `HotkeyService.__init__`
  _范围_: `services/hotkey_service.py:1-25` | _依赖_: 06, 09, 10 | _测试_: `tests/services/test_hotkey_service.py::test_init`
  - `class HotkeyService`：接收 `keyboard_hook` 模块、`log_service: LogService`、`macro_engine: MacroEngine`
  - 跟踪 `_current_start_key: str | None`、`_current_stop_key: str | None`、`_current_scheme: Scheme | None`

- [ ] **12.2** 实现内部 `_on_start()` 和 `_on_stop()` 回调
  _范围_: `services/hotkey_service.py:27-45` | _依赖_: 12.1 | _测试_: `tests/services/test_hotkey_service.py::test_on_start_calls_engine`
  - `_on_start(self)`：记录热键按下日志，调用 `macro_engine.start(self._current_scheme)`
  - `_on_stop(self)`：记录热键按下日志，调用 `macro_engine.stop()`
  - 设计决策：添加 `_current_scheme` 属性，在 `register_for_scheme` 时设置

- [ ] **12.3** 实现 `register_for_scheme()`
  _范围_: `services/hotkey_service.py:47-75` | _依赖_: 12.2 | _测试_: `tests/services/test_hotkey_service.py::test_register_hotkeys`（mock）
  - `def register_for_scheme(self, scheme: Scheme) -> None`
  - 先调用 `unregister_current()` 清除旧绑定
  - 存储 `_current_scheme = scheme`
  - 通过 `keyboard_hook.register_hotkey(scheme.start_hotkey, self._on_start)` 注册
  - 通过 `keyboard_hook.register_hotkey(scheme.stop_hotkey, self._on_stop)` 注册
  - 跟踪 `_current_start_key`、`_current_stop_key`
  - 记录注册事件日志

- [ ] **12.4** 实现 `unregister_current()` 和 `clear()`
  _范围_: `services/hotkey_service.py:77-100` | _依赖_: 12.3 | _测试_: `tests/services/test_hotkey_service.py::test_unregister`（mock）
  - `unregister_current()`：注销当前 start 和 stop 键（如已设置），然后置为 None
  - `clear()`：调用 `unregister_current()` 后 `keyboard_hook.clear_all()`
  - 测试：注册后注销，验证 keyboard_hook.unregister_hotkey 以正确参数被调用

---

**完成标准**: register/unregister 生命周期正常，回调正确路由到 macro_engine。
