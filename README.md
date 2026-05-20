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
pip install -r requirements.txt
python main.py
```

或直接运行 `dist/游戏按键自动化工具.exe`。

## 技术栈

Python 3.11+ · Tkinter · SQLite · pydirectinput · keyboard · PyInstaller

## 项目结构

```
├── models/        数据模型（Action / Scheme 冻结数据类）
├── infra/         基础设施（输入模拟 / 热键钩子 / 数据库 / 预设方案）
├── services/      业务逻辑（宏引擎 / 方案管理 / 热键协调 / 日志）
├── ui/            表现层（主窗口 / 方案编辑器 / 各控件）
├── tests/         437 个单元测试（覆盖率 97%）
├── doc/           设计文档与任务说明
├── app.py         依赖组装
├── main.py        程序入口
└── build.spec     打包配置
```

## 测试

```bash
pytest tests/ -v --cov=.
```
