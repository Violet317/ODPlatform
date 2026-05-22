#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :test_paths.py
# @Time      :2026/5/19
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :路径工具单元测试

from pathlib import Path

import pytest

from odp_platform.common.paths import (
    _find_workspace_root,
    get_dirs_to_initialize,
)
from odp_platform.common.paths import WORKSPACE_MARKER


class TestFindWorkspaceRoot:
    """测试工作区根目录探测功能。"""

    def test_find_root_from_subdir(self, tmp_path):
        """在子目录中调用，应向上找到 marker 所在目录。"""
        workspace = tmp_path / "my_workspace"
        workspace.mkdir()
        (workspace / WORKSPACE_MARKER).touch()

        subdir = workspace / "apps" / "platform" / "src"
        subdir.mkdir(parents=True)

        root = _find_workspace_root(subdir)
        assert root == workspace

    def test_find_root_from_marker_dir(self, tmp_path):
        """在包含 marker 的目录中调用，应返回自身。"""
        workspace = tmp_path / "my_workspace"
        workspace.mkdir()
        (workspace / WORKSPACE_MARKER).touch()

        root = _find_workspace_root(workspace)
        assert root == workspace

    def test_file_not_found_error(self, tmp_path):
        """在没有任何 marker 的目录树中调用，应抛出 FileNotFoundError。"""
        orphan = tmp_path / "orphan" / "deep"
        orphan.mkdir(parents=True)

        with pytest.raises(FileNotFoundError):
            _find_workspace_root(orphan)

    def test_start_from_file(self, tmp_path):
        """起始路径是文件时，应从其父目录开始查找。"""
        workspace = tmp_path / "my_workspace"
        workspace.mkdir()
        (workspace / WORKSPACE_MARKER).touch()

        some_file = workspace / "a_file.txt"
        some_file.touch()

        root = _find_workspace_root(some_file)
        assert root == workspace


class TestGetDirsToInitialize:
    """测试 get_dirs_to_initialize 返回的路径列表。"""

    def test_returns_list_of_paths(self):
        """应返回 Path 列表。"""
        dirs = get_dirs_to_initialize()
        assert isinstance(dirs, list)
        assert all(isinstance(d, Path) for d in dirs)

    def test_all_under_root(self):
        """所有路径都应在 ROOT_DIR 之下。"""
        from odp_platform.common.paths import ROOT_DIR

        dirs = get_dirs_to_initialize()
        for d in dirs:
            # 不抛出异常即表示在 ROOT_DIR 之下
            d.relative_to(ROOT_DIR)

    def test_no_duplicates(self):
        """返回的列表不应包含重复路径。"""
        dirs = get_dirs_to_initialize()
        assert len(dirs) == len(set(dirs)), "存在重复目录路径"