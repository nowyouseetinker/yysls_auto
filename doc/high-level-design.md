# 游戏按键自动化工具 - 概要设计文档

**版本**: v1.1
**日期**: 2026-05-21
**状态**: 已确认

## 1. 设计目标

基于需求文档 [proposal.md](proposal.md)，将系统划分为 5 层 17 个模块，遵循单向依赖、高内聚低耦合的设计原则。每个模块职责单一，文件控制在 400 行以内。

## 2. 技术栈选型

| 层 | 技术 | 说明 |
|----|------|------|
| 语言 | Python 3.11+ | 用户指定 |
| GUI | Tkinter | Python 标准库自带，无需额外安装 |
| 数据库 | SQLite + sqlite3 | Python 标准库自带 |
| 输入模拟 | pydirectinput | 通过 DirectInput API 发送输入，兼容全屏 3D 游戏 |
| 全局热键 | keyboard | Windows 底层键盘钩子 |
| 提权 | ctypes.windll.shell32 | 调用 Windows ShellExecuteW 请求管理员权限 |
| 打包 | PyInstaller | 生成独立单文件 EXE |
| 测试 | pytest + pytest-cov | 项目标准 |
| 代码质量 | black + isort + ruff | 项目标准 |

**外部依赖仅 2 个**：`pydirectinput`、`keyboard`（均为纯 Python + Windows 原生轮子）。

## 3. 模块划分

### 3.1 分层架构

```
┌─────────────────────────────────┐
│  main.py / app.py   (入口层)     │
├─────────────────────────────────┤
│  ui/                 (表现层)    │
│  main_window, scheme_editor,    │
│  widgets/*                      │
├─────────────────────────────────┤
│  services/          (业务逻辑层) │
│  macro_engine, scheme_service,  │
│  hotkey_service, log_service    │
├─────────────────────────────────┤
│  infra/            (基础设施层)  │
│  admin, input_simulator,        │
│  keyboard_hook, db_repository,  │
│  preset_repository              │
├─────────────────────────────────┤
│  models/            (数据模型层) │
│  enums, action, scheme          │
└─────────────────────────────────┘
```

依赖方向：入口 → 表现层 → 业务逻辑层 → 基础设施层 → 数据模型层。严格单向，无循环。

### 3.2 Layer 1: 数据模型层 (models/)

| 模块 | 文件 | 职责 |
|------|------|------|
| 枚举定义 | `models/enums.py` | `ActionType`(KEY_PRESS/MOUSE_CLICK/WAIT)、`MouseButton`(LEFT/RIGHT) |
| 操作模型 | `models/action.py` | `Action` 冻结数据类，按类型区分字段，含工厂方法、验证、描述 |
| 方案模型 | `models/scheme.py` | `Scheme` 冻结数据类，含名称、操作列表、热键、循环标志、预设标记 |

### 3.3 Layer 2: 基础设施层 (infra/)

| 模块 | 文件 | 职责 |
|------|------|------|
| 权限管理 | `infra/admin.py` | `is_admin()` 检查管理员权限；`elevate()` 通过 UAC 提权重启 |
| 输入模拟 | `infra/input_simulator.py` | 封装 `pydirectinput`：`press_key()`、`click_mouse()`、`interruptible_sleep()` |
| 键盘钩子 | `infra/keyboard_hook.py` | 封装 `keyboard` 库：`register_hotkey()`、`unregister_hotkey()`、`clear_all()` |
| 数据库仓储 | `infra/db_repository.py` | SQLite CRUD：建表、增删改查，Action 与 JSON 双向序列化 |
| 预设仓储 | `infra/preset_repository.py` | 定义 4 套只读预设方案，作为模块级常量 |

### 3.4 Layer 3: 业务逻辑层 (services/)

| 模块 | 文件 | 职责 |
|------|------|------|
| 宏引擎 | `services/macro_engine.py` | 守护线程执行操作序列，`threading.Event` 停止信号，0.1s 轮询可中断等待 |
| 方案服务 | `services/scheme_service.py` | 聚合预设+自定义方案，CRUD 编排，验证，禁止修改预设 |
| 热键服务 | `services/hotkey_service.py` | 热键注册/注销生命周期，在引擎和钩子之间协调 |
| 日志服务 | `services/log_service.py` | 线程安全的日志队列（deque + Lock），支持订阅回调 |

### 3.5 Layer 4: 表现层 (ui/)

| 模块 | 文件 | 职责 |
|------|------|------|
| 主窗口 | `ui/main_window.py` | 根窗口，组合所有 widget，50ms 定时刷新 UI，协调模块间交互 |
| 方案编辑器 | `ui/scheme_editor.py` | 模态弹窗，方案名称/热键/循环设置，操作步骤列表编辑（增/删/排序/改参） |
| 方案列表 | `ui/widgets/scheme_list.py` | 列表控件，显示所有方案（区分预设/自定义），选中事件 |
| 步骤预览 | `ui/widgets/step_preview.py` | 只读列表，显示当前方案的操作步骤描述 |
| 日志区 | `ui/widgets/log_area.py` | 只读文本框，订阅 LogService 回调，带时间戳，自动滚动 |
| 状态栏 | `ui/widgets/status_bar.py` | 方案名、热键、运行状态指示灯、运行时长、启停按钮 |

### 3.6 Layer 5: 入口层

| 模块 | 文件 | 职责 |
|------|------|------|
| 程序入口 | `main.py` | 管理员权限检查与提权，调用 `app.create_app()` |
| 依赖组装 | `app.py` | 创建所有实例并注入依赖，返回 Tk 根窗口 |

## 4. 模块依赖关系

```
main.py
  └─ app.py
       ├─ models/enums.py           (叶子)
       ├─ models/action.py          (依赖 enums)
       ├─ models/scheme.py          (依赖 action, enums)
       ├─ infra/admin.py            (叶子，仅 ctypes)
       ├─ infra/input_simulator.py  (叶子，依赖 pydirectinput + enums)
       ├─ infra/keyboard_hook.py    (叶子，仅 keyboard)
       ├─ infra/db_repository.py    (叶子，依赖 sqlite3 + models)
       ├─ infra/preset_repository.py(叶子，仅 models)
       ├─ services/log_service.py   (叶子，仅 threading)
       ├─ services/macro_engine.py  (依赖 input_simulator, log_service, models)
       ├─ services/scheme_service.py(依赖 db_repository, preset_repository, models)
       ├─ services/hotkey_service.py(依赖 keyboard_hook, macro_engine, log_service, models)
       ├─ ui/main_window.py         (依赖所有 services, 所有 widgets)
       ├─ ui/scheme_editor.py       (依赖 models)
       └─ ui/widgets/*.py           (依赖 models)
```

## 5. 数据结构

### 5.1 Action（操作步骤）

```python
@dataclass(frozen=True)
class Action:
    action_type: ActionType        # KEY_PRESS | MOUSE_CLICK | WAIT
    order: int                     # 步骤序号
    # 键盘/鼠标共用
    key: str | None                # 按键名 (KEY_PRESS 时必填)
    mouse_button: MouseButton | None  # 鼠标按钮 (MOUSE_CLICK 时必填)
    duration: float = 0.1          # 按下持续时间
    # 等待专用（互斥：固定 或 随机范围）
    wait_seconds: float | None     # 固定等待秒数
    wait_min: float | None         # 随机等待最小值
    wait_max: float | None         # 随机等待最大值
```

工厂方法：`Action.key_press(key, order, duration)`、`Action.mouse_click(button, order, duration)`、`Action.wait_fixed(seconds, order)`、`Action.wait_random(min_s, max_s, order)`

### 5.2 Scheme（方案）

```python
@dataclass(frozen=True)
class Scheme:
    id: str                        # UUID4 或预设固定 ID
    name: str                      # 方案名称
    description: str               # 方案描述
    actions: tuple[Action, ...]    # 操作步骤（不可变，非空）
    loop: bool                     # 是否循环
    start_hotkey: str              # 启动热键
    stop_hotkey: str               # 停止热键
    is_preset: bool                # 是否内置预设
```

### 5.3 数据库表结构

```sql
CREATE TABLE schemes (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    description   TEXT NOT NULL DEFAULT '',
    actions_json  TEXT NOT NULL,          -- JSON 数组
    loop          INTEGER NOT NULL DEFAULT 1,
    start_hotkey  TEXT NOT NULL DEFAULT 'F10',
    stop_hotkey   TEXT NOT NULL DEFAULT 'F12',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## 6. 数据流

### 6.1 启动宏

```
用户按 F10 / 点 [启动]
  → HotkeyService.start_macro()
    → 检查 MacroEngine.is_running（防重复）
    → MacroEngine.start(current_scheme)
      → 清空 stop_event
      → 启动 daemon 线程 _execute(scheme)
        → while not stopped:
            → for action in scheme.actions:
                → LogService.add("执行：...")
                → dispatch: KEY_PRESS→InputSimulator.press_key()
                            MOUSE_CLICK→InputSimulator.click_mouse()
                            WAIT→interruptible_sleep()  # 可中断
      → GUI 50ms tick: 更新状态灯 + 运行时长
```

### 6.2 停止宏

```
用户按 F12 / 点 [停止]
  → HotkeyService.stop_macro()
    → MacroEngine.stop()
      → stop_event.set()
      → 工作线程在 ≤0.1s 内检测到并退出
      → LogService.add("⏹ 已停止")
```

### 6.3 创建自定义方案

```
用户点 [新建方案]
  → main_window 打开 scheme_editor (mode="create")
    → 用户填写名称、热键、循环开关
    → 用户 [添加步骤] → 选类型 → 填参数 → Action 追加到列表
    → 用户 [上移/下移] 调整顺序
    → 用户 [保存]
      → 构造 Scheme(id=uuid4(), is_preset=False)
      → SchemeService.create_scheme() → 验证 → DbRepository.save()
      → 关闭弹窗，返回新 Scheme
  → main_window 刷新方案列表
```

### 6.4 复制预设方案

```
用户选中预设 → 点 [复制方案]
  → main_window 打开 scheme_editor (mode="create")
    → 以预设的 name + " (副本)"、actions、hotkeys 等预填充
    → 用户修改后保存 → 同新建流程
```

### 6.5 导出方案

```
用户选中方案 → 点 [导出方案]
  → main_window._on_export_scheme()
    → scheme.to_export_string()
      → to_dict() → JSON → base64 编码
    → root.clipboard_clear() + root.clipboard_append()
    → 弹出 "已复制到剪贴板" 提示
```

### 6.6 导入方案

```
用户点 [导入方案]
  → main_window._on_import_scheme()
    → 弹出导入对话框（Text 输入框）
    → 用户粘贴 base64 字符串 → 点 [导入]
    → Scheme.from_export_string(raw)
      → base64 解码 → JSON 解析 → 字段提取
      → Scheme.create() 生成新 UUID
    → SchemeService.create_scheme() → 持久化
    → 刷新方案列表 → 弹出 "导入成功" 提示
```

### 6.7 切换方案

```
用户在列表中点击方案
  → SchemeList 触发 <<SchemeSelected>>
  → main_window.on_scheme_selected(scheme):
    → 如果在运行中，提示需先停止（阻止切换）
    → HotkeyService.unregister_current()
    → HotkeyService.register_hotkeys(scheme)
    → StepPreview.set_scheme(scheme)
    → StatusBar.update_state(scheme=scheme)
    → 设置为 current_scheme
```

## 7. 线程模型

系统共 2 个线程：

| 线程 | 职责 | 所属 |
|------|------|------|
| 主线程 | Tkinter 事件循环 + 50ms 定时 UI 刷新 | GUI |
| 工作线程 | 执行操作序列 | MacroEngine daemon thread |

**同步机制**：

| 机制 | 用途 |
|------|------|
| `threading.Event` | 停止信号。主线程 set，工作线程检查 |
| `threading.Lock` | LogService deque 写入保护 |
| Tkinter `after()` | 工作线程不接触 widget，由主线程定时刷新 |
| 不可变数据 | Scheme/Action 为 frozen dataclass，跨线程安全读取 |

> `keyboard` 库的热键回调运行在库自有的线程上，回调只调用 `MacroEngine.start()`/`stop()`，两者内部是线程安全的。

## 8. 4 套预设方案

| ID | 名称 | 操作序列 | 热键 |
|----|------|----------|------|
| preset_zha_yu | 炸鱼 | 按键4 → 等22~24秒(随机) → 循环 | F10/F12 |
| preset_xi_shuai | 蟋蟀 | 左键 → 等100秒 → 空格 → 等5秒 → F → 等5秒 → 循环 | F10/F12 |
| preset_gather | 自动采集 | 按键1 → 等10~12秒(随机) → 循环 | F10/F12 |
| preset_clicker | 连点器 | F → 等0.15秒 → 循环 | F10/F12 |

预设方案内置于 `infra/preset_repository.py`，标记 `is_preset=True`，只读不可修改。用户可通过「复制方案」将其复制为自定义方案后编辑。

## 9. 文件大小估算

| 文件 | 预估行数 |
|------|----------|
| models/enums.py | ~15 |
| models/action.py | ~80 |
| models/scheme.py | ~60 |
| infra/admin.py | ~30 |
| infra/input_simulator.py | ~40 |
| infra/keyboard_hook.py | ~50 |
| infra/db_repository.py | ~120 |
| infra/preset_repository.py | ~100 |
| services/macro_engine.py | ~100 |
| services/scheme_service.py | ~120 |
| services/hotkey_service.py | ~80 |
| services/log_service.py | ~60 |
| ui/main_window.py | ~300 |
| ui/scheme_editor.py | ~350 |
| ui/widgets/*.py (4个) | ~100 每个 |
| app.py | ~50 |
| main.py | ~20 |

所有文件均不超过 400 行，满足项目编码规范要求。

## 10. 方案导出与导入（紧凑格式）

### 10.1 导出格式

```
Scheme → _action_to_compact() → 紧凑 JSON（短键名 + 省略默认值/order） → base64 → ASCII 字符串
```

**紧凑格式说明**：

| 原始键 | 紧凑键 | 说明 |
|--------|--------|------|
| `name` | `n` | 方案名称 |
| `description` | `d` | 描述（为空时省略） |
| `actions` | `a` | 动作数组 |
| `action_type` | `t` | 0=KEY_PRESS, 1=MOUSE_CLICK, 2=WAIT固定, 3=WAIT随机 |
| `key` | `k` | 按键名 |
| `mouse_button` | `m` | 0=LEFT, 1=RIGHT |
| `duration` | `d` | 仅当非 0.1 时编码 |
| `wait_seconds` | `s` | 固定等待秒数 |
| `wait_min` / `wait_max` | `n` / `x` | 随机等待范围 |
| `loop` | `l` | 仅当非循环时编码（`l:0`） |
| `start_hotkey` | `sh` | 仅当非 F10 时编码 |
| `stop_hotkey` | `st` | 仅当非 F12 时编码 |
| `order` | — | 不编码，导入时从数组索引重建 |

6 步方案约 **280B**（原始 1.4KB），10 步方案约 **308B**（原始 2.0KB）。

### 10.2 导入流程

```
用户粘贴 base64 字符串
  → Scheme.from_export_string()
    → base64.b64decode() → json.loads()
    → _action_from_compact() 逐条重建 Action（order 从索引赋值）
    → Scheme.create(name, description, actions, loop, hotkeys)
    → 生成全新 UUID4 id，is_preset=False
  → SchemeService.create_scheme() → DbRepository.save()
  → 刷新方案列表
```

### 10.3 关键约束

- 预设方案也**可以导出**，但导入后得到的永远是**自定义方案**（`is_preset=False`，新 UUID）
- 导入时方案名称不自动去重，用户可后续通过编辑器改名
- 无效的 base64 / JSON / 缺少必要字段会弹出明确中文错误

---

## 11. 与需求功能的覆盖关系

| 需求编号 | 需求功能 | 对应模块 |
|----------|----------|----------|
| F1 | 热键启停 | hotkey_service + keyboard_hook + macro_engine |
| F2 | 预设方案库 | preset_repository + scheme_list |
| F3 | 自定义方案 | scheme_editor + scheme_service |
| F4 | 方案管理 | scheme_service + db_repository + scheme_list |
| F5 | 游戏兼容 | input_simulator (pydirectinput) + admin (提权) |
| F6 | EXE 打包 | build.spec (PyInstaller) |
| F7 | 方案导出/导入 | scheme (to_export_string / from_export_string) + main_window (导出/导入按钮) |
