# 21-build — PyInstaller .spec

**目标文件**: `build.spec` (~40 行)
**预估时间**: 10-15 分钟
**依赖**: 20-main（main.py 可正常运行）

---

- [ ] **21.1** 创建 `build.spec` 单文件 EXE 配置
  _范围_: `build.spec` | _依赖_: 20 | _测试_: `pyinstaller build.spec` 生成可运行 EXE
  - `Analysis`：scripts=["main.py"]，包含所有项目 .py 文件
  - Hidden imports：`pydirectinput`、`keyboard`、`json`、`threading`、`ctypes`
  - `EXE`：单文件，console=False（GUI 应用隐藏控制台窗口）
  - 名称设为 "游戏按键自动化工具"
  - 验证生成的 EXE 能启动并正常工作
  - 校验：EXE 大小 < 50MB

---

**完成标准**: `pyinstaller build.spec` 生成独立 EXE（< 50MB），启动 GUI 正常。
