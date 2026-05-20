# 16-status-bar — ui/widgets/status_bar.py

**目标文件**: `ui/widgets/status_bar.py` (~100 行)
**预估时间**: 20-25 分钟
**依赖**: 01-03 models（仅需 Scheme 模型）

---

- [ ] **16.1** 实现 `StatusBarWidget.__init__` 和布局
  _范围_: `ui/widgets/status_bar.py:1-45` | _依赖_: 03 | _测试_: `tests/ui/test_status_bar.py::test_widget_creation`
  - 继承 `tkinter.Frame`，grid 布局，单行 6 格
  - 标签：方案名（`Label`，左对齐）、热键显示（`Label`）、状态指示器（`Label`，"○" 或 "●"）、已运行时间（`Label`，"00:00:00"）
  - 按钮：`tkinter.Button` "启动" 和 "停止"，初始停止按钮禁用
  - 接收回调：`on_start: Callable`、`on_stop: Callable`

- [ ] **16.2** 实现 `update_state()` 方法
  _范围_: `ui/widgets/status_bar.py:47-70` | _依赖_: 16.1 | _测试_: `tests/ui/test_status_bar.py::test_update_state`
  - `def update_state(self, scheme_name=None, hotkeys=None, is_running=None, elapsed_seconds=None) -> None`
  - 仅更新提供了非 None 值的标签（部分更新模式）
  - 状态指示器：运行时显示 "● 运行中"（绿色），空闲时显示 "○ 空闲"（灰色）
  - 时间格式化为 "HH:MM:SS"

- [ ] **16.3** 实现 `_format_elapsed()` 辅助方法
  _范围_: `ui/widgets/status_bar.py:72-85` | _依赖_: 16.2 | _测试_: `tests/ui/test_status_bar.py::test_format_elapsed`
  - `def _format_elapsed(self, seconds: float) -> str`：返回 `f"{hours:02d}:{minutes:02d}:{secs:02d}"`
  - 测试：0 → "00:00:00"，3661.0 → "01:01:01"，86399.0 → "23:59:59"

- [ ] **16.4** 实现按钮启用/禁用状态管理
  _范围_: `ui/widgets/status_bar.py:87-105` | _依赖_: 16.3 | _测试_: `tests/ui/test_status_bar.py::test_button_states`
  - 未运行时启动按钮启用，运行时禁用
  - 运行时停止按钮启用，未运行时禁用
  - `update_state(is_running=True)` 启用停止、禁用启动；反之亦然
  - 测试按钮状态转换

---

**完成标准**: 所有标签更新正常，状态指示器切换正确，按钮启用/禁用逻辑正确。
