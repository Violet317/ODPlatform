#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :init_project.py
# @Time      :2026/5/19 10:28:46
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :ODPlatform 项目初始化入口（开发阶段）

"""
ODPlatform 项目初始化入口（开发阶段）

使用方法:
    python init_project.py              # 初始化目录
    python init_project.py --reset      # 重置运行时数据（交互确认）
    python init_project.py --reset --force  # 强制重置
    python -m odp_platform.cli.init_project  # 等价调用

说明:
    1. 将 apps/platform/src 加入 sys.path
    2. 调用 odp_platform.cli.init_project.initialize_project()
    3. 创建所有必要的运行时目录
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PLATFORM_SRC = REPO_ROOT / "apps" / "platform" / "src"

sys.path.insert(0, str(PLATFORM_SRC))

from odp_platform import __version__
from odp_platform.cli.init_project import initialize_project, reset_project


def main():
    parser = argparse.ArgumentParser(description="ODPlatform 项目初始化工具")
    parser.add_argument("--version", action="version", version=f"ODPlatform v{__version__}")
    parser.add_argument("--reset", action="store_true", help="重置运行时数据（清空 runs/ 和 logs/）")
    parser.add_argument("--force", action="store_true", help="跳过确认直接执行重置")
    args = parser.parse_args()

    if args.reset:
        reset_project(confirm=args.force)
    else:
        initialize_project()


if __name__ == "__main__":
    main()