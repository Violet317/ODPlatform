#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :conftest.py
# @Time      :2026/5/19
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :pytest 共享夹具定义

import sys
import pytest
from pathlib import Path

# 在 conftest 模块级别将 platform/src 加入 sys.path
# 这样在测试模块 import 之前就能找到 odp_platform 包
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))


@pytest.fixture
def tmp_workspace(tmp_path):
    """创建一个临时工作区用于测试。"""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    (workspace / ".odp-workspace").touch()
    return workspace


@pytest.fixture
def sample_class_names():
    """返回测试用的样本类别名称列表。"""
    return ["aircraft", "ship", "storage_tank", "baseball_diamond"]