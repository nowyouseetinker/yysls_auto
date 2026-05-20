# 08-preset-repository — infra/preset_repository.py

**目标文件**: `infra/preset_repository.py` (~100 行)
**预估时间**: 20-25 分钟
**依赖**: 01-enums, 02-action, 03-scheme（数据模型）

---

- [ ] **08.1** 定义 4 套预设方案的名称/ID 模块级常量
  _范围_: `infra/preset_repository.py:1-15` | _依赖_: 01, 02, 03 | _测试_: `tests/infra/test_preset_repository.py::test_preset_ids_unique`
  - 定义 `PRESET_IDS = {"zha_yu": "preset_zha_yu", "xi_shuai": "preset_xi_shuai", "gather": "preset_gather", "clicker": "preset_clicker"}`
  - 验证 4 个 key 各不相同

- [ ] **08.2** 实现 `_build_preset_zha_yu()` 私有函数
  _范围_: `infra/preset_repository.py:17-30` | _依赖_: 08.1 | _测试_: `tests/infra/test_preset_repository.py::test_preset_zha_yu_structure`
  - 构建：`Action.key_press("4", order=0)` → `Action.wait_random(22, 24, order=1)`
  - `Scheme.create_preset(id=PRESET_IDS["zha_yu"], name="炸鱼", loop=True, actions=(key4, wait22_24))`
  - 测试：验证 name、loop、actions 数量、is_preset=True

- [ ] **08.3** 实现 `_build_preset_xi_shuai()` 私有函数
  _范围_: `infra/preset_repository.py:32-55` | _依赖_: 08.2 | _测试_: `tests/infra/test_preset_repository.py::test_preset_xi_shuai_structure`
  - 构建 6 个 action：左键点击 → 等 100s → 空格 → 等 5s → F → 等 5s
  - Scheme name="蟋蟀"，loop=True
  - 测试：6 个 action，类型和参数正确

- [ ] **08.4** 实现 `_build_preset_gather()` 和 `_build_preset_clicker()`
  _范围_: `infra/preset_repository.py:57-80` | _依赖_: 08.3 | _测试_: `tests/infra/test_preset_repository.py::test_preset_gather`, `test_preset_clicker`
  - gather：`Action.key_press("1", 0)` → `Action.wait_random(10, 12, 1)`，name="自动采集"
  - clicker：`Action.key_press("F", 0)` → `Action.wait_fixed(0.15, 1)`，name="连点器"
  - 两者 loop=True，is_preset=True

- [ ] **08.5** 实现 `get_all_presets()` 和 `get_preset_by_id()`
  _范围_: `infra/preset_repository.py:82-100` | _依赖_: 08.4 | _测试_: `tests/infra/test_preset_repository.py::test_get_all_presets`
  - `def get_all_presets() -> list[Scheme]`：返回全部 4 套预设方案
  - `def get_preset_by_id(id: str) -> Scheme | None`：按 id 线性搜索
  - 测试：get_all 返回 4 项；get_preset_by_id 对有效/无效 ID 均正确

---

**完成标准**: 4 套预设方案结构正确，get_all 返回 4，get_by_id 正确工作。
