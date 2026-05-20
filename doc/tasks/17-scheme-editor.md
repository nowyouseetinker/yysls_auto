# 17-scheme-editor — ui/scheme_editor.py

**目标文件**: `ui/scheme_editor.py` (~300 行)
**预估时间**: 45-60 分钟
**依赖**: 01-03 models（Action/Scheme 模型）

---

- [ ] **17.1** 实现 `SchemeEditorDialog.__init__` 和基本布局
  _范围_: `ui/scheme_editor.py:1-50` | _依赖_: 02, 03 | _测试_: `tests/ui/test_scheme_editor.py::test_dialog_creation`
  - 继承 `tkinter.Toplevel`，设为模态（`grab_set()`、`transient(parent)`）
  - 构造函数：`__init__(self, parent, mode: str = "create", scheme: Scheme | None = None)`
  - 标题："新建方案" 或 "编辑方案"
  - 表单字段：名称（`Entry`）、启动热键（`Entry`，默认 "F10"）、停止热键（`Entry`，默认 "F12"）、循环（`Checkbutton`，默认选中）
  - 编辑模式下用 scheme 数据预填充字段

- [ ] **17.2** 实现 action 列表展示区
  _范围_: `ui/scheme_editor.py:52-80` | _依赖_: 17.1 | _测试_: `tests/ui/test_scheme_editor.py::test_action_list_display`
  - 创建 `Listbox` 显示 action 列表（高度 8），展示 `str(action)`
  - 存储 `self._actions: list[Action]` 为可变列表
  - 编辑模式时从 `scheme.actions` 元组转换为列表并填充
  - 绑定选择事件

- [ ] **17.3** 实现 action 工具栏：添加和删除按钮
  _范围_: `ui/scheme_editor.py:82-115` | _依赖_: 17.2 | _测试_: `tests/ui/test_scheme_editor.py::test_add_action`
  - "添加步骤" 按钮：打开子对话框（使用内联下拉菜单+字段 或 小 Toplevel）
  - 设计决策：使用 `_add_action_dialog()` 打开小 Toplevel，包含类型选择器（`OptionMenu`）和参数字段
  - 确认后：通过工厂方法创建 Action，追加到 `self._actions`，刷新 Listbox，重编号 order
  - "删除" 按钮：从列表中移除选中的 action，刷新

- [ ] **17.4** 实现上移/下移按钮
  _范围_: `ui/scheme_editor.py:117-140` | _依赖_: 17.3 | _测试_: `tests/ui/test_scheme_editor.py::test_move_action_up`
  - "上移" / "下移" 按钮：将选中 action 与相邻项交换
  - 每次移动后更新 `action.order` 字段
  - 刷新 Listbox 显示
  - 首项禁用上移，末项禁用下移

- [ ] **17.5** 实现编辑 Action 按钮
  _范围_: `ui/scheme_editor.py:142-165` | _依赖_: 17.4 | _测试_: `tests/ui/test_scheme_editor.py::test_edit_action`
  - "编辑" 按钮：打开与添加相同的子对话框，用选中 action 的当前值预填充
  - 确认后：替换列表中的 action，刷新显示

- [ ] **17.6** 实现 `_add_action_dialog()` 子对话框
  _范围_: `ui/scheme_editor.py:167-220` | _依赖_: 17.5 | _测试_: `tests/ui/test_scheme_editor.py::test_add_action_dialog_returns_action`
  - 小 Toplevel，包含类型选择 `OptionMenu`："按键"、"鼠标点击"、"固定等待"、"随机等待"
  - 根据类型动态显示字段（用 `pack_forget` 隐藏/显示）
  - 按键：key 字段 + duration；鼠标：按钮选择器 + duration；固定等待：seconds；随机等待：min/max
  - "确定" / "取消" 按钮
  - 返回 `Action | None`

- [ ] **17.7** 实现 `_validate_and_save()` 方法
  _范围_: `ui/scheme_editor.py:222-250` | _依赖_: 17.6 | _测试_: `tests/ui/test_scheme_editor.py::test_validate_empty_name`
  - 验证：name 非空、actions 非空、start_hotkey 非空、stop_hotkey 非空、start != stop
  - 每种验证失败时使用 `messagebox.showerror` 提示
  - 成功后：构造 Scheme（新建或更新已有），设置 `self.result = scheme`，关闭对话框
  - 取消时 `result` 为 None

- [ ] **17.8** 实现取消按钮和对话框结果协议
  _范围_: `ui/scheme_editor.py:252-270` | _依赖_: 17.7 | _测试_: `tests/ui/test_scheme_editor.py::test_cancel_returns_none`
  - "取消" 按钮：设置 `self.result = None`，销毁对话框
  - 协议：调用方使用 `parent.wait_window(dialog)` 后通过 `dialog.result` 获取 Scheme 或 None
  - 覆盖 `destroy()` 处理清理

---

**完成标准**: 完整的创建和编辑流程可用，验证触发，action 列表 CRUD 功能正常。
