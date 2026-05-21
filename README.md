# 游戏按键自动化工具

Windows 桌面 GUI 工具，让玩家在全屏游戏中通过热键启动/停止自动化的键盘鼠标操作序列（宏）。

## 功能

- **热键启停** — 全局热键（默认 F10/F12）一键启动/停止宏执行
- **预设方案库** — 内置 4 套即选即用方案（炸鱼、蟋蟀、自动采集、连点器）
- **自定义方案** — 通过 GUI 编辑器自由编排按键/鼠标/等待操作序列
- **方案导出/导入** — 方案以紧凑字符串导出到剪贴板，跨电脑快速分享
- **游戏兼容** — 使用 DirectInput API 模拟输入，适配全屏 3D 游戏
- **单文件 EXE** — PyInstaller 打包为独立可执行文件，无需 Python 环境

## 快速开始

```bash
pip install customtkinter pydirectinput keyboard
python main.py
```

或直接下载 Releases 中的 `yysls_auto_v1.2.exe` 运行。

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| GUI | **CustomTkinter 5.2+**（现代化扁平 UI） |
| 数据库 | SQLite |
| 输入模拟 | pydirectinput（DirectInput API） |
| 全局热键 | keyboard |
| 打包 | PyInstaller（单文件 EXE） |

## 构建 EXE

```bash
# 先跑测试再打包
python build.py --test

# 或仅打包
python build.py
```

输出：`dist/游戏按键自动化工具.exe`

## 项目结构

```
├── models/        数据模型（Action / Scheme 冻结数据类）
├── infra/         基础设施（输入模拟 / 热键钩子 / 数据库 / 预设方案）
├── services/      业务逻辑（宏引擎 / 方案管理 / 热键协调 / 日志）
├── ui/            表现层（主题 / 主窗口 / 方案编辑器 / 各控件）
│   ├── theme.py         全局主题配置（颜色 / 字体 / 按钮预设）
│   ├── main_window.py   主窗口（PanedWindow 分割预览/日志）
│   ├── scheme_editor.py 方案编辑器（三阶弹窗）
│   └── widgets/         控件（方案列表 / 步骤预览 / 日志 / 状态栏）
├── tests/         306 个核心单元测试
├── doc/           设计文档与任务说明
├── app.py         依赖组装
├── main.py        程序入口
├── build.py       一键构建脚本
└── build.spec     PyInstaller 配置
```

## 测试

```bash
# 核心业务逻辑测试
pytest tests/infra/ tests/models/ tests/services/ -q

# 全部测试（含 UI 层，需要桌面环境）
pytest tests/ -v --cov=.
```
