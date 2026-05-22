#!/usr/bin/env python
# @FileName  :__init__.py
# @Time      :2026/5/19 09:58:22
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :ODPlatform - 通用的目标检测开发平台
"""
ODPlatform - Object Detection Platform Core Engine.

Public API 入口，具体的子模块：
    odp_platform.common       : 基础工具（路径、日志、字符串、系统、性能）
    odp_platform.data_pipeline: 数据管道（Pascal VOC / COCO / YOLO 格式转换）
    odp_platform.cli          : 命令行入口（odp-* 系列命令）
"""

from odp_platform._version import __version__

__all__ = ["__version__"]
