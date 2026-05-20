# 10-macro-engine — services/macro_engine.py

**目标文件**: `services/macro_engine.py` (~105 行)
**预估时间**: 25-35 分钟
**依赖**: 05-input-simulator, 09-log-service, 01-03 models

---

- [ ] **10.1** 实现 `MacroEngine.__init__` 和 `is_running`
  _范围_: `services/macro_engine.py:1-30` | _依赖_: 05, 09 | _测试_: `tests/services/test_macro_engine.py::test_init_not_running`
  - `class MacroEngine`：接收 `input_simulator` 模块（或具体函数）和 `log_service: LogService`
  - `self._stop_event = threading.Event()`，`self._thread: threading.Thread | None = None`
  - `is_running` 属性返回 `self._thread is not None and self._thread.is_alive()`
  - 测试：新实例 is_running == False

- [ ] **10.2** 实现 `start()` 方法
  _范围_: `services/macro_engine.py:32-55` | _依赖_: 10.1 | _测试_: `tests/services/test_macro_engine.py::test_start_creates_thread`
  - `def start(self, scheme: Scheme) -> None`
  - 验证未在运行中（如已运行抛出 RuntimeError）
  - 清除 stop_event，创建 daemon `threading.Thread(target=self._execute, args=(scheme,))`，启动
  - 通过 `log_service.add()` 记录启动事件
  - 测试：启动 scheme，验证线程存活，is_running == True

- [ ] **10.3** 实现 `_execute()` 主循环
  _范围_: `services/macro_engine.py:57-85` | _依赖_: 10.2 | _测试_: `tests/services/test_macro_engine.py::test_execute_loop`
  - `def _execute(self, scheme: Scheme) -> None`
  - 外层循环：`while not self._stop_event.is_set():`（若 `not scheme.loop` 则单次通过）
  - 内层循环：`for action in scheme.actions:`，每个 action 前检查 stop_event
  - 每个 action：log `"执行：{action}"`，调用 `_dispatch_action(action)`
  - 内层循环中途停止时干净退出
  - 自然结束或停止时记录日志

- [ ] **10.4** 实现 `_dispatch_action()` 路由
  _范围_: `services/macro_engine.py:87-110` | _依赖_: 10.3 | _测试_: `tests/services/test_macro_engine.py::test_dispatch_key_press`（mock simulator）
  - 按 `action.action_type` 路由：
    - KEY_PRESS：调用 `press_key(action.key, action.duration)`
    - MOUSE_CLICK：调用 `click_mouse(action.mouse_button.value, action.duration)`
    - WAIT (fixed)：调用 `interruptible_sleep(action.wait_seconds, self._stop_event)`，返回 False 则停止
    - WAIT (random)：`seconds = random.uniform(action.wait_min, action.wait_max)`，调用 `interruptible_sleep(seconds, self._stop_event)`
  - Mock input_simulator，验证正确函数被调用且参数正确

- [ ] **10.5** 实现 `stop()` 方法
  _范围_: `services/macro_engine.py:112-130` | _依赖_: 10.4 | _测试_: `tests/services/test_macro_engine.py::test_stop`
  - `def stop(self) -> None`：set stop_event，log "已停止"
  - 不调用 `thread.join()` 无超时（会卡死），最多 2s 超时
  - 测试：启动 engine，停止 engine，验证 0.5s 内 is_running 变为 False

---

**完成标准**: start/stop 生命周期正常，action 路由分发正确，stop event 可中断 sleep。
