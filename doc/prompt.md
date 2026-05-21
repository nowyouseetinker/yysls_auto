# Vibe Coding Prompt: 游戏按键自动化工具

**角色**: 你是一个主控 Agent（Orchestrator），负责协调整个项目的构建、测试和集成。你**不直接写代码**，而是通过派发子 Agent 来完成每个模块的实现和测试。整个过程完全自动化，无需人工参与。

---

## 1. 项目概述

构建一个 Windows 桌面 GUI 工具，让玩家在全屏游戏中通过热键启动/停止自动化的键盘鼠标操作序列（宏）。用户可以通过图形界面选择预设方案或自定义编排操作序列。

核心功能：
- **F1 热键启停**: 全局热键启动/停止宏执行
- **F2 预设方案库**: 4 套内置只读方案，即选即用
- **F3 自定义方案**: GUI 编辑器新建/编辑/删除自定义操作序列
- **F4 方案管理**: 预设与自定义方案统一列表管理
- **F5 游戏兼容**: DirectInput 方式发送按键，适配全屏/3D 游戏
- **F6 EXE 打包**: PyInstaller 打包为独立可执行文件
- **F7 方案导出/导入**: 方案以 base64 编码字符串导出到剪贴板，支持跨电脑快速分享与导入

---

## 2. 参考文档

在开始之前，主控 Agent 必须**先阅读**以下文档以全面了解项目：

| 文档 | 路径 | 内容 |
|------|------|------|
| 需求文档 | `doc/proposal.md` | 完整功能需求、UI 布局、用户流程 |
| 概要设计 | `doc/high-level-design.md` | 分层架构、模块划分、数据结构、数据流、线程模型 |
| 任务划分 | `doc/tasks/progress.md` | 21 个模块的任务列表、阶段划分、依赖关系、关键路径 |
| 详细任务 | `doc/tasks/01-enums.md` ~ `doc/tasks/21-build.md` | 每个模块的具体子任务、测试要求、完成标准 |

---

## 3. 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | 使用 `from __future__ import annotations` |
| GUI | **CustomTkinter 5.2+** | 现代化扁平 UI，替代标准 Tkinter |
| 数据库 | SQLite (sqlite3) | Python 标准库 |
| 输入模拟 | pydirectinput | 外部依赖 |
| 全局热键 | keyboard | 外部依赖 |
| 打包 | PyInstaller | 生成单文件 EXE |
| 测试 | pytest + pytest-cov | 目标覆盖率 80%+ |
| 类型检查 | mypy (strict 模式) | 0 错误容忍 |
| Lint | ruff | 0 错误容忍 |
| 格式化 | black + isort | 统一代码风格 |

---

## 4. 项目结构

```
yysls_auto/
├── models/
│   ├── __init__.py
│   ├── enums.py              # ActionType, MouseButton 枚举
│   ├── action.py             # Action 冻结数据类
│   └── scheme.py             # Scheme 冻结数据类
├── infra/
│   ├── __init__.py
│   ├── admin.py              # 管理员权限检查与提权
│   ├── input_simulator.py    # 封装 pydirectinput
│   ├── keyboard_hook.py      # 封装 keyboard 库
│   ├── db_repository.py      # SQLite CRUD
│   └── preset_repository.py  # 4 套只读预设方案
├── services/
│   ├── __init__.py
│   ├── log_service.py        # 线程安全日志服务
│   ├── macro_engine.py       # 宏执行引擎（守护线程）
│   ├── scheme_service.py     # 方案管理业务逻辑
│   └── hotkey_service.py     # 热键注册与生命周期
├── ui/
│   ├── __init__.py
│   ├── main_window.py        # 主窗口，组合所有 widget
│   ├── scheme_editor.py      # 方案编辑器模态弹窗
│   └── widgets/
│       ├── __init__.py
│       ├── scheme_list.py    # 方案列表控件
│       ├── step_preview.py   # 步骤预览控件
│       ├── log_area.py       # 日志区控件
│       └── status_bar.py     # 状态栏控件
├── tests/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── test_enums.py
│   │   ├── test_action.py
│   │   └── test_scheme.py
│   ├── infra/
│   │   ├── __init__.py
│   │   ├── test_admin.py
│   │   ├── test_input_simulator.py
│   │   ├── test_keyboard_hook.py
│   │   ├── test_db_repository.py
│   │   └── test_preset_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── test_log_service.py
│   │   ├── test_macro_engine.py
│   │   ├── test_scheme_service.py
│   │   └── test_hotkey_service.py
│   └── ui/
│       ├── __init__.py
│       ├── test_scheme_list.py
│       ├── test_step_preview.py
│       ├── test_log_area.py
│       ├── test_status_bar.py
│       ├── test_scheme_editor.py
│       └── test_main_window.py
├── app.py                    # 依赖组装工厂
├── main.py                   # 程序入口
├── build.spec                # PyInstaller 配置
├── ui/theme.py               # 全局主题配置（颜色、字体、按钮预设）
├── app.py                    # 依赖组装工厂
├── main.py                   # 程序入口
├── build.spec                # PyInstaller 配置
├── pyproject.toml            # 项目配置（ruff, mypy, black, isort）
└── doc/                      # 文档目录
```

---

## 5. 架构与依赖

### 5.1 分层架构（严格单向依赖）

```
入口层:   main.py → app.py
表现层:   ui/main_window.py, ui/scheme_editor.py, ui/widgets/*
业务层:   services/macro_engine.py, scheme_service.py, hotkey_service.py, log_service.py
基础层:   infra/input_simulator.py, keyboard_hook.py, db_repository.py, preset_repository.py, admin.py
模型层:   models/enums.py, action.py, scheme.py
```

### 5.2 关键设计原则

- **不可变数据**: Action 和 Scheme 都是 `@dataclass(frozen=True)`，跨线程安全
- **线程模型**: 主线程（Tkinter）+ 工作线程（宏执行 daemon thread），共 2 个线程
- **同步**: `threading.Event`（停止信号）、`threading.Lock`（日志队列保护）、Tkinter `after()` 定时刷新
- **预设保护**: `is_preset=True` 的方案禁止修改/删除
- **依赖注入**: `app.py` 中创建所有实例并注入
- **CustomTkinter UI**: 使用 CustomTkinter 替代标准 Tkinter，全局扁平化主题通过 `ui/theme.py` 配置（颜色常量、懒加载字体、按钮预设）。所有 `CTkFont` 在根窗口创建后按需初始化以避免导入时 `RuntimeError`。
- **方案导出/导入（紧凑格式）**: `Scheme.to_export_string()` 使用短键名 + 省略默认值 + base64，6 步方案仅 ~280B（原始 1.4KB）；`Scheme.from_export_string()` 解码并用新 UUID 创建方案，`order` 从数组索引重建

---

## 6. 构建计划（7 个阶段，21 个模块）

### Phase 1: 数据模型层（串行，有依赖）

| 序号 | 模块 | 文件 | 依赖 | 预估 |
|------|------|------|------|------|
| 01 | 枚举定义 | `models/enums.py` | 无 | 10min |
| 02 | 操作模型 | `models/action.py` | 01 | 35min |
| 03 | 方案模型 | `models/scheme.py` | 01, 02 | 25min |

### Phase 2: 基础设施层（可并行，均依赖 Phase 1）

| 序号 | 模块 | 文件 | 依赖 | 预估 |
|------|------|------|------|------|
| 04 | 权限管理 | `infra/admin.py` | 无 | 15min |
| 05 | 输入模拟 | `infra/input_simulator.py` | 01 | 20min |
| 06 | 键盘钩子 | `infra/keyboard_hook.py` | 无 | 20min |
| 07 | 数据库仓储 | `infra/db_repository.py` | 01, 02, 03 | 40min |
| 08 | 预设仓储 | `infra/preset_repository.py` | 01, 02, 03 | 25min |

### Phase 3: 核心服务层（部分可并行）

| 序号 | 模块 | 文件 | 依赖 | 预估 |
|------|------|------|------|------|
| 09 | 日志服务 | `services/log_service.py` | 无 | 20min |
| 10 | 宏引擎 | `services/macro_engine.py` | 05, 09, 01-03 | 35min |
| 11 | 方案服务 | `services/scheme_service.py` | 07, 08, 01-03 | 35min |

### Phase 4: 协调服务

| 序号 | 模块 | 文件 | 依赖 | 预估 |
|------|------|------|------|------|
| 12 | 热键服务 | `services/hotkey_service.py` | 06, 09, 10, 01-03 | 25min |

### Phase 5: UI Widgets（可并行）

| 序号 | 模块 | 文件 | 依赖 | 预估 |
|------|------|------|------|------|
| 13 | 方案列表 | `ui/widgets/scheme_list.py` | 03 | 20min |
| 14 | 步骤预览 | `ui/widgets/step_preview.py` | 02 | 15min |
| 15 | 日志区 | `ui/widgets/log_area.py` | 09 | 20min |
| 16 | 状态栏 | `ui/widgets/status_bar.py` | 03 | 25min |

### Phase 6: UI 窗口

| 序号 | 模块 | 文件 | 依赖 | 预估 |
|------|------|------|------|------|
| 17 | 方案编辑器 | `ui/scheme_editor.py` | 02, 03 | 60min |
| 18 | 主窗口 | `ui/main_window.py` | 09-16 | 50min |

### Phase 7: 入口与构建

| 序号 | 模块 | 文件 | 依赖 | 预估 |
|------|------|------|------|------|
| 19 | 依赖组装 | `app.py` | 全部 infra + services + ui | 15min |
| 20 | 程序入口 | `main.py` | 04, 19 | 10min |
| 21 | PyInstaller | `build.spec` | 20 | 15min |

---

## 7. 主控 Agent 执行流程

### 7.1 初始化

1. 读取所有参考文档（proposal.md, high-level-design.md, progress.md, 所有 task md）
2. 确认项目目录结构
3. 初始化 pyproject.toml（包含 ruff、mypy、black、isort 配置和 pytest 配置）
4. 初始化空的 `__init__.py` 文件和 tests 目录结构

### 7.2 逐阶段执行

对每个 Phase，按以下规则执行：

**规则 1 - 顺序依赖**: 同一 Phase 内，如模块有依赖关系，按依赖顺序串行执行。如模块无依赖关系，**并行**派发子 Agent。

**规则 2 - Phase 间**: 每个 Phase 全部完成后，主控 Agent 验证该 Phase 所有模块的测试通过 + mypy + ruff 检查通过，然后才能进入下一 Phase。

**规则 3 - 子 Agent 任务**: 每个子 Agent 负责：
- 阅读对应 `doc/tasks/XX-module.md` 中的详细任务描述
- 实现模块代码
- 编写完整的 pytest 单元测试
- 运行测试并确保全部通过
- 修复任何 mypy 类型错误和 ruff lint 错误
- 完成后向主控 Agent 报告结果

### 7.3 子 Agent 调用格式

对每个模块，使用 `Agent` 工具派发子 Agent：

```
Agent(
  description: "实现 XX 模块",
  subagent_type: "general-purpose",
  prompt: """
  实现模块 {module_name}。
  
  详细任务说明见: doc/tasks/{task_file}.md
  设计文档见: doc/high-level-design.md
  需求文档见: doc/proposal.md
  
  你必须:
  1. 先阅读 doc/tasks/{task_file}.md 了解所有子任务
  2. 实现 {file_path}
  3. 编写 {test_file_path} 中的完整 pytest 测试
  4. 运行 pytest {test_file_path} -v 确保全部通过
  5. 运行 ruff check {file_path} {test_file_path} 确保无错误
  6. 运行 mypy {file_path} 确保类型检查通过
  7. 向主控 Agent 报告完成情况
  """
)
```

### 7.4 Phase 完成验证

每个 Phase 完成后，主控 Agent 运行：
```bash
# 运行该 Phase 涉及的所有测试文件
pytest tests/{phase_dir}/ -v --cov={package} --cov-report=term-missing

# 运行 ruff 检查该 Phase 的所有源文件
ruff check {phase_files}

# 运行 mypy 检查该 Phase 的所有源文件
mypy {phase_files}
```

验证通过后方可进入下一 Phase。若不通过，分析失败原因，派发子 Agent 修复。

### 7.5 进度跟踪

主控 Agent 在每个模块完成后更新 `doc/tasks/progress.md`，勾选对应的任务项。

### 7.6 最终验证

所有 21 个模块完成后，运行：
```bash
# 完整测试
pytest tests/ -v --cov=. --cov-report=term-missing

# 完整 lint
ruff check .

# 完整类型检查
mypy .

# 验证覆盖率 >= 80%
```

---

## 8. 并行执行指南

以下模块**必须在同一 Phase 内并行派发**以节省时间：

**Phase 2 并行组**（Phase 1 完成后）:
```
04-admin  +  05-input-simulator  +  06-keyboard-hook  +  07-db-repository  +  08-preset-repository
(04, 05, 06 可立即并行；07, 08 也并行因为它们只依赖 Phase 1)
```

**Phase 3 并行组**:
```
09-log-service  +  10-macro-engine  +  11-scheme-service
(全部可以并行，因为 09 无依赖，10 和 11 依赖不同模块)
```

**Phase 5 并行组**:
```
13-scheme-list  +  14-step-preview  +  15-log-area  +  16-status-bar
(全部可以并行)
```

---

## 9. 代码质量要求

### 9.1 必须遵守的规范

- 所有函数 < 50 行
- 所有文件 < 800 行（目标 200-400 行）
- 使用 `@dataclass(frozen=True)` 保持不可变性
- 使用 early return 避免深层嵌套（>4 层）
- 所有错误显式处理，不静默吞异常
- 无硬编码密钥或凭据
- 不可变数据模式（创建新对象，不修改已有对象）

### 9.2 pyproject.toml 配置

```toml
[project]
name = "yysls-auto"
version = "1.0.0"
requires-python = ">=3.11"

[tool.ruff]
target-version = "py311"
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.ruff.isort]
known-first-party = ["models", "infra", "services", "ui"]

[tool.mypy]
strict = true
python_version = "3.11"
warn_unreachable = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-v --tb=short"

[tool.black]
line-length = 100

[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["models", "infra", "services", "ui"]
```

---

## 10. 关键注意事项

1. **Tkinter 线程安全**: 只有主线程可以操作 Tkinter widget。子线程（宏引擎、keyboard 回调）必须通过 Tkinter 的 `after()` 或 `event_generate()` 与 UI 通信。

2. **可中断等待**: `interruptible_sleep()` 必须以 0.1s 步长轮询 `stop_event`，确保停止键响应延迟 < 0.2s。

3. **预设方案保护**: `is_preset=True` 的方案在所有修改/删除操作前必须被拦截。

4. **管理员权限**: `main.py` 启动时检查，非管理员则通过 UAC 提权重启。

5. **Scheme Editor 的 mode 参数**: `mode="create"` 新建空白方案，`mode="edit"` 编辑已有自定义方案（预填充数据）。编辑预设方案时先复制为自定义方案。

6. **数据库线程安全**: SQLite 连接使用 `check_same_thread=False`。

7. **日志回调线程安全**: LogService 的回调可能来自非主线程，UI widget 中必须用 `after(0, ...)` 调度到主线程更新。

8. **方案导出/导入（紧凑格式）**: `models/scheme.py` 中的 `to_export_string()` 将方案编码为紧凑 JSON（短键名如 `n`/`a`/`t`/`k`/`m`，省略 `order`/默认时长/默认热键），再 base64 编码。6 步方案从 1.4KB 压缩至 ~280B。导入时 `from_export_string()` 通过 `_action_from_compact()` 解码，调用 `Scheme.create()` 生成全新 UUID。工具栏「导出方案」「导入方案」按钮在 `ui/main_window.py` 中实现。

9. **CustomTkinter 注意事项**:
   - `CTkFont` 不能在根窗口创建前实例化。`ui/theme.py` 使用懒加载字典 + 函数工厂，字体在首次调用 `label_font()` / `small_font()` 等时按需创建。
   - `CTkTextbox.tag_config()` **不支持 `font` 参数**（因缩放兼容性），只能设置 `foreground` 颜色。如需不同字体尺寸，通过 `CTkTextbox` 构造时的 `font=` 统一设定。
   - `CTkScrollableFrame` 的滚动条通过 `scrollbar_fg_color` / `scrollbar_button_color` 控制。`pack_forget()` 不可靠，改用按钮颜色切换（内容适合时设为与背景同色以隐藏）。
   - 右侧 PanedWindow 使用标准 `tk.PanedWindow`（CTk 无对应组件），需通过 `.sash_place()` 设置初始比例。
   - 所有按钮通过 `ui/theme.py` 中的 `BTN_DEFAULT` / `BTN_PRIMARY` / `BTN_SUCCESS` / `BTN_DANGER` 预设字典统一配置，字体在调用处显式设置。'

---

## 11. 开始执行

主控 Agent，现在开始执行。请按以下步骤操作：

1. 读取 `doc/proposal.md`、`doc/high-level-design.md`、`doc/tasks/progress.md`
2. 初始化项目基础文件（pyproject.toml、`__init__.py` 文件、tests 目录结构）
3. 从 **Phase 1** 开始，按顺序执行 01-enums → 02-action → 03-scheme
4. 每个模块派发一个子 Agent 完成实现+测试
5. Phase 1 全部完成后验证，然后继续 Phase 2
6. 按此模式推进直至所有 21 个模块完成
7. 最终运行全量测试 + lint + 类型检查，验证通过
