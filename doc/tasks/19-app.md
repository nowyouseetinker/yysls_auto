# 19-app — app.py

**目标文件**: `app.py` (~50 行)
**预估时间**: 10-15 分钟
**依赖**: 全部 infra + 全部 services + 全部 ui

---

- [ ] **19.1** 实现 `create_app()` 工厂函数 — 实例化基础设施层
  _范围_: `app.py:1-30` | _依赖_: 全部 infra + services | _测试_: `tests/test_app.py::test_create_app_returns_root`
  - `def create_app() -> tkinter.Tk`
  - 按顺序实例化：
    - `db_repo = DbRepository()`
    - `log_service = LogService()`
    - `macro_engine = MacroEngine(input_simulator, log_service)`
    - `scheme_service = SchemeService(db_repo, preset_repository)`
    - `hotkey_service = HotkeyService(keyboard_hook, log_service, macro_engine)`
  - 验证每个实例化成功

- [ ] **19.2** 完成 `create_app()` — 实例化 UI 并返回 root
  _范围_: `app.py:31-55` | _依赖_: 19.1 | _测试_: 手动运行
  - 创建 `root = tkinter.Tk()`
  - 创建 `MainWindow(root, scheme_service, hotkey_service, macro_engine, log_service)`
  - 返回 `root`
  - 测试：验证函数返回 Tk 实例，所有 services 非 None

---

**完成标准**: `root = create_app(); root.mainloop()` 启动完整应用。
