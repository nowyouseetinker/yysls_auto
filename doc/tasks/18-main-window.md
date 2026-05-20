# 18-main-window — ui/main_window.py

**目标文件**: `ui/main_window.py` (~270 行)
**预估时间**: 35-50 分钟
**依赖**: 全部 services (09-12) + 全部 widgets (13-16)

---

- [ ] **18.1** 实现 `MainWindow.__init__` 和依赖注入
  _范围_: `ui/main_window.py:1-45` | _依赖_: 全部 services | _测试_: `tests/ui/test_main_window.py::test_window_creation`（集成测试）
  - `class MainWindow`：构造函数接收所有 service 实例
  - `__init__(self, root, scheme_service, hotkey_service, macro_engine, log_service)`
  - 存储 services 为属性
  - 设置 `self._current_scheme: Scheme | None = None`
  - 窗口标题 "游戏按键自动化工具"，尺寸 700x600，最小尺寸 600x400

- [ ] **18.2** 实现 `_setup_ui()` 布局
  _范围_: `ui/main_window.py:47-90` | _依赖_: 18.1 | _测试_: 视觉检查
  - 实例化 4 个 widget（scheme_list、step_preview、log_area、status_bar），传入正确的 parent 和依赖
  - 使用 `grid` 布局：
    - Column 0：scheme_list（row 0，rowspan 2）
    - Column 1：step_preview（row 0）、log_area（row 1）
    - Row 2：status_bar 跨两列
  - 配置 grid weights 支持响应式缩放

- [ ] **18.3** 实现 `_refresh_loop()` 和 50ms 定时器
  _范围_: `ui/main_window.py:92-110` | _依赖_: 18.2 | _测试_: `tests/ui/test_main_window.py::test_refresh_timer`
  - `def _refresh_loop(self) -> None`
  - 由 `self.after(50, self._refresh_loop)` 每 50ms 调用
  - 若 macro 运行中，更新 `status_bar.update_state(elapsed_seconds=...)`
  - 用 `time.monotonic()` 跟踪启动时间计算已运行时长
  - 通过 `self.after(50, self._refresh_loop)` 调度下次调用

- [ ] **18.4** 实现 `_on_scheme_selected()` 处理函数
  _范围_: `ui/main_window.py:112-135` | _依赖_: 18.3 | _测试_: `tests/ui/test_main_window.py::test_on_scheme_selected`
  - 处理来自 scheme_list widget 的 `<<SchemeSelected>>` 虚拟事件
  - 若 macro 正在运行，`messagebox.showwarning("请先停止当前方案")`，返回
  - 从 scheme_list 获取 scheme，设置 `self._current_scheme`
  - 调用 `hotkey_service.register_for_scheme(scheme)`（先注销旧再注册新）
  - 调用 `step_preview.set_scheme(scheme)`、`status_bar.update_state(scheme_name=scheme.name, hotkeys=f"{scheme.start_hotkey}/{scheme.stop_hotkey}")`

- [ ] **18.5** 实现工具栏按钮：新建、编辑、删除方案
  _范围_: `ui/main_window.py:137-175` | _依赖_: 18.4 | _测试_: `tests/ui/test_main_window.py::test_toolbar_buttons`（mock editor）
  - 创建工具栏 Frame，含 3 个按钮 + "复制方案" 按钮
  - `_on_new_scheme()`：打开 SchemeEditorDialog(mode="create")，若有结果，调用 `scheme_service.create_scheme(result)`，刷新列表
  - `_on_edit_scheme()`：需要选中方案，若为预设则提示复制为自定义方案（或禁用按钮）
  - `_on_delete_scheme()`：需要选中方案，拒绝预设，`messagebox.askyesno` 确认，调用 `scheme_service.delete_scheme(id)`，刷新列表
  - `_on_copy_preset()`：打开编辑器，预填充预设数据，mode="create"

- [ ] **18.6** 实现启动/停止按钮处理函数
  _范围_: `ui/main_window.py:177-200` | _依赖_: 18.5 | _测试_: `tests/ui/test_main_window.py::test_start_stop_buttons`
  - `_on_start()`：需要选中方案，调用 `macro_engine.start(current_scheme)`，记录启动时间
  - `_on_stop()`：调用 `macro_engine.stop()`
  - 两者均通过 `status_bar.update_state(is_running=...)` 更新状态栏

- [ ] **18.7** 实现 `refresh_scheme_list()` 和初始化序列
  _范围_: `ui/main_window.py:202-230` | _依赖_: 18.6 | _测试_: 集成测试
  - `def refresh_scheme_list(self) -> None`：从 service 获取所有方案，调用 `scheme_list.refresh(schemes)`
  - 初始化：调用 `refresh_scheme_list()`、选中第一个预设、启动刷新定时器
  - 设置虚拟事件绑定
  - 若无方案选中，状态栏显示空闲状态

---

**完成标准**: 窗口正确渲染，方案选择/编辑流程端到端可用，50ms 定时器正常更新。
