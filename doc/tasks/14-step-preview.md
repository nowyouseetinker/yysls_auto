# 14-step-preview — ui/widgets/step_preview.py

**目标文件**: `ui/widgets/step_preview.py` (~55 行)
**预估时间**: 12-18 分钟
**依赖**: 01-03 models（仅需 Action/Scheme 模型）

---

- [ ] **14.1** 实现 `StepPreviewWidget.__init__` 和布局
  _范围_: `ui/widgets/step_preview.py:1-30` | _依赖_: 02 | _测试_: `tests/ui/test_step_preview.py::test_widget_creation`
  - 继承 `tkinter.Frame`，创建标题标签 "操作步骤预览"
  - 创建只读 `Listbox` 和滚动条（`state="disabled"` 禁用用户交互）
  - 设置固定高度（8-10 行）

- [ ] **14.2** 实现 `set_scheme()` 方法
  _范围_: `ui/widgets/step_preview.py:32-50` | _依赖_: 14.1 | _测试_: `tests/ui/test_step_preview.py::test_set_scheme_populates`
  - `def set_scheme(self, scheme: Scheme) -> None`
  - 启用 Listbox 编辑，清空，插入每个 action 的 `__str__()` 输出
  - 格式：`"{idx+1}. {str(action)}"`
  - 填充完成后重新禁用 Listbox
  - 测试：传入含 5 个 action 的 Scheme

- [ ] **14.3** 实现 `clear()` 方法
  _范围_: `ui/widgets/step_preview.py:52-60` | _依赖_: 14.2 | _测试_: `tests/ui/test_step_preview.py::test_clear`
  - `def clear(self) -> None`：清空 Listbox
  - 测试：set scheme 后 clear，验证 Listbox size 为 0

---

**完成标准**: 方案步骤以只读编号列表显示，clear 正常。
