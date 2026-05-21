#!/usr/bin/env python3
"""一键构建 EXE — 清理旧构建 → 打包 → 复制为 yysls_auto_v1.2.exe

用法:
    python build.py            # 构建
    python build.py --test     # 先跑测试，测试通过后再构建
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
SPEC = os.path.join(ROOT, "build.spec")
EXE_NAME = "游戏按键自动化工具.exe"
VERSION_EXE = "yysls_auto_v1.2.exe"


def run(cmd: list[str], desc: str) -> None:
    print(f"\n── {desc} ──")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"❌ {desc} 失败 (exit={result.returncode})")
        sys.exit(result.returncode)
    print(f"✅ {desc} 通过")


def main() -> None:
    # ── 可选：先跑测试 ──────────────────────────────────────────
    if "--test" in sys.argv:
        run(["python", "-m", "pytest", "tests/infra/", "tests/models/", "tests/services/",
             "-q", "--tb=short"], "运行核心测试")

    # ── 清理旧的 build 目录 ────────────────────────────────────
    build_dir = os.path.join(ROOT, "build")
    if os.path.isdir(build_dir):
        print("\n── 清理 build 目录 ──")
        shutil.rmtree(build_dir)
        print("✅ 已清理")

    # ── PyInstaller 打包 ────────────────────────────────────────
    run(["pyinstaller", SPEC], "PyInstaller 打包")

    # ── 复制为带版本号的文件 ────────────────────────────────────
    src = os.path.join(DIST, EXE_NAME)
    dst = os.path.join(DIST, VERSION_EXE)
    if os.path.isfile(src):
        shutil.copy2(src, dst)
        src_size = os.path.getsize(src) / (1024 * 1024)
        print(f"\n✅ 构建完成！")
        print(f"   {EXE_NAME}  ({src_size:.1f} MB)")
        print(f"   {VERSION_EXE}  (副本)")
    else:
        print(f"❌ 未找到 {src}")
        sys.exit(1)


if __name__ == "__main__":
    main()
