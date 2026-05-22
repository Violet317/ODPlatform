#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :reset_project.py
# @Time      :2026/5/19
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :odp-reset 命令行入口（薄壳脚本）

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLATFORM_SRC = REPO_ROOT / "apps" / "platform" / "src"

sys.path.insert(0, str(PLATFORM_SRC))

from odp_platform.cli.reset_project import main

if __name__ == "__main__":
    sys.exit(main())