# 20-main — main.py

**目标文件**: `main.py` (~20 行)
**预估时间**: 5-10 分钟
**依赖**: 04-admin, 19-app

---

- [ ] **20.1** 实现带管理员权限检查和应用启动的入口点
  _范围_: `main.py:1-25` | _依赖_: 04, 19 | _测试_: 手动运行（无法单元测试 UAC + Tk）
  - `def main() -> None`
  - `if not is_admin(): elevate()`
  - `root = create_app()`
  - `root.mainloop()`
  - `if __name__ == "__main__": main()`
  - 确保 `elevate()` 调用 `sys.exit()`，非管理员进程不会到达 `create_app()`

---

**完成标准**: 运行 `python main.py` 启动应用（根据环境可能触发 UAC 提权）。
