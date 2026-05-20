# 04-admin — infra/admin.py

**目标文件**: `infra/admin.py` (~25 行)
**预估时间**: 10-15 分钟
**依赖**: 无（叶子模块，仅 ctypes）

---

- [ ] **04.1** 实现 `is_admin()` 函数
  _范围_: `infra/admin.py:1-15` | _依赖_: 无 | _测试_: `tests/infra/test_admin.py::test_is_admin_returns_bool`
  - `def is_admin() -> bool`：调用 `ctypes.windll.shell32.IsUserAnAdmin()`，返回布尔值
  - 用 try/except 包裹，出错时返回 False
  - 测试：验证返回值为 bool 类型（实际值取决于运行环境，无法断言 True/False）

- [ ] **04.2** 实现 `elevate()` 函数
  _范围_: `infra/admin.py:17-35` | _依赖_: 04.1 | _测试_: 仅手动测试（需要实际 UAC）
  - `def elevate() -> None`：调用 `ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)`，然后 `sys.exit()`
  - 仅在 `not is_admin()` 时调用，否则无操作
  - 添加说明 UAC 行为的 docstring
  - 标记 `# pragma: no cover`（无法单元测试 UAC 提权）

---

**完成标准**: `is_admin()` 在运行时返回布尔值，`elevate()` 逻辑经代码审查正确。
