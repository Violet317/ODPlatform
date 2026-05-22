#!/usr/bin/env python
# @FileName  :system_utils.py
# @Time      :2026/5/19
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :系统工具 —— 获取系统信息、GPU 状态、磁盘使用

import platform
import shutil


def get_system_info() -> dict:
    """获取系统信息。"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }


def check_gpu_available() -> bool:
    """检查 GPU 是否可用。"""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def get_disk_usage(path: str = ".") -> dict:
    """获取磁盘使用信息。"""
    usage = shutil.disk_usage(path)
    return {
        "total_gb": usage.total / (1024**3),
        "used_gb": usage.used / (1024**3),
        "free_gb": usage.free / (1024**3),
    }


def log_device_info(logger) -> None:
    """记录当前系统设备信息到日志。"""
    info = get_system_info()
    logger.info(f"操作系统: {info['system']} {info['release']} ({info['machine']})")
    logger.info(f"Python   : {info['python_version']}")

    disk = get_disk_usage(".")
    logger.info(f"磁盘使用: 总 {disk['total_gb']:.1f} GB, 已用 {disk['used_gb']:.1f} GB, 剩余 {disk['free_gb']:.1f} GB")

    gpu = check_gpu_available()
    logger.info(f"GPU 状态: {'可用' if gpu else '不可用'}")
