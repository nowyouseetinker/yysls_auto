# 09-log-service — services/log_service.py

**目标文件**: `services/log_service.py` (~55 行)
**预估时间**: 15-20 分钟
**依赖**: 无（叶子模块，仅 threading + collections）

---

- [ ] **09.1** 实现 `LogService.__init__` 和数据结构
  _范围_: `services/log_service.py:1-25` | _依赖_: 无 | _测试_: `tests/services/test_log_service.py::test_init_empty`
  - `class LogService`：`self._logs: deque[dict] = deque(maxlen=500)`，`self._lock = threading.Lock()`，`self._subscribers: list[Callable] = []`
  - 每条日志格式：`{"timestamp": str, "message": str}`
  - 测试：新实例 deque 为空

- [ ] **09.2** 实现 `add()` 方法
  _范围_: `services/log_service.py:27-45` | _依赖_: 09.1 | _测试_: `tests/services/test_log_service.py::test_add_log`
  - `def add(self, message: str) -> None`
  - 线程安全：获取锁，追加带 `isoformat` 时间戳 + 消息的字典
  - 追加后在锁外调用每个订阅者的回调（先在锁内复制订阅者列表，避免死锁）
  - 测试：添加 2 条消息，验证 deque 长度和时间戳

- [ ] **09.3** 实现 `subscribe()`、`unsubscribe()`、`get_logs()`
  _范围_: `services/log_service.py:47-65` | _依赖_: 09.2 | _测试_: `tests/services/test_log_service.py::test_subscribe_callback`
  - `def subscribe(self, callback: Callable[[dict], None]) -> None`：追加到订阅者列表
  - `def unsubscribe(self, callback: Callable[[dict], None]) -> None`：从订阅者列表移除
  - `def get_logs(self) -> list[dict]`：返回 deque 的列表副本（线程安全快照）
  - 测试：订阅回调，添加日志，验证回调被调用且参数正确

- [ ] **09.4** 实现 `clear()` 方法
  _范围_: `services/log_service.py:67-75` | _依赖_: 09.3 | _测试_: `tests/services/test_log_service.py::test_clear`
  - `def clear(self) -> None`：线程安全清空 deque
  - 测试：添加消息，清空，get_logs 返回空列表

---

**完成标准**: 全部 4 个子任务完成，线程安全通过测试验证。
