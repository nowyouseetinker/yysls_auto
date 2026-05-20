# 15-log-area — ui/widgets/log_area.py

**目标文件**: `ui/widgets/log_area.py` (~70 行)
**预估时间**: 15-20 分钟
**依赖**: 09-log-service, 01-03 models

---

- [ ] **15.1** 实现 `LogAreaWidget.__init__` 和布局
  _范围_: `ui/widgets/log_area.py:1-35` | _依赖_: 09 | _测试_: `tests/ui/test_log_area.py::test_widget_creation`
  - 继承 `tkinter.Frame`，创建标题标签 "日志"
  - 创建 `tkinter.scrolledtext.ScrolledText`，`state="disabled"`（只读），高度 ~10 行
  - 构造函数接收 `log_service: LogService`
  - 在 `__init__` 中调用 `log_service.subscribe(self._on_new_log)`

- [ ] **15.2** 实现 `_on_new_log()` 回调
  _范围_: `ui/widgets/log_area.py:37-55` | _依赖_: 15.1 | _测试_: `tests/ui/test_log_area.py::test_log_callback_appends_text`
  - `def _on_new_log(self, entry: dict) -> None`
  - 启用 widget 编辑，在末尾插入 `f"[{entry['timestamp']}] {entry['message']}\n"`
  - 自动滚动到末尾：`self._text.see(tkinter.END)`
  - 重新禁用 widget
  - 注意：log_service 回调可能来自其他线程，Tkinter 要求主线程更新 widget
  - 方案：使用 `self.after(0, lambda: self._append_to_widget(entry))` 调度到主线程

- [ ] **15.3** 实现 `clear()` 方法和订阅/取消订阅生命周期
  _范围_: `ui/widgets/log_area.py:57-75` | _依赖_: 15.2 | _测试_: `tests/ui/test_log_area.py::test_clear`
  - `def clear(self) -> None`：清空文本 widget 内容
  - 实现 `destroy()` 覆盖或 `on_close()` 来取消订阅 log_service，防止泄漏
  - 测试：通过 log_service 添加条目后 clear，验证 widget 清空

---

**完成标准**: 日志带时间戳显示，自动滚动，主线程调度正常。
