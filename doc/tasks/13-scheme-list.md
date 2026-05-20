# 13-scheme-list — ui/widgets/scheme_list.py

**目标文件**: `ui/widgets/scheme_list.py` (~85 行)
**预估时间**: 20-25 分钟
**依赖**: 01-03 models（仅需 Scheme 模型）

---

- [ ] **13.1** 实现 `SchemeListWidget.__init__` 和布局
  _范围_: `ui/widgets/scheme_list.py:1-40` | _依赖_: 03 | _测试_: 视觉检查 + `tests/ui/test_scheme_list.py::test_widget_creation`
  - 继承 `tkinter.Frame`，创建 `Listbox` 和滚动条（pack 布局）
  - 添加标题标签 "方案列表"
  - 设置 `selectmode="browse"`（单选）
  - 绑定 `<<ListboxSelect>>` 到内部处理函数

- [ ] **13.2** 实现 `refresh()` 方法
  _范围_: `ui/widgets/scheme_list.py:42-65` | _依赖_: 13.1 | _测试_: `tests/ui/test_scheme_list.py::test_refresh_populates_list`
  - `def refresh(self, schemes: list[Scheme]) -> None`
  - 清空 Listbox，按以下格式插入每个 scheme：`"[预设] {name}"` 或 `"[自定义] {name}"`
  - 将 schemes 存入字典 `self._scheme_map = {index: Scheme}` 供后续检索
  - 测试：传入 4 preset + 2 custom 的列表

- [ ] **13.3** 实现 `get_selected()` 和 `_on_select()`
  _范围_: `ui/widgets/scheme_list.py:67-85` | _依赖_: 13.2 | _测试_: `tests/ui/test_scheme_list.py::test_get_selected_returns_scheme`
  - `get_selected(self) -> Scheme | None`：返回选中的 Scheme 或 None
  - `_on_select(self, event)`：在 widget 上生成虚拟事件 `<<SchemeSelected>>`
  - 测试：选择某个 index，验证 get_selected 返回正确的 Scheme

---

**完成标准**: 列表可填充，选择获取正确，虚拟事件正确触发。
