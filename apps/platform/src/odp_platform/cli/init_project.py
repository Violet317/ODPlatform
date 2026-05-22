#!/usr/bin/env python
# @FileName  :init_project.py
# @Time      :2026/5/18 11:34:37
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :项目初始化 —— 创建所有运行时目录

import logging
from pathlib import Path

from odp_platform.common.logging_utils import get_logger
from odp_platform.common.paths import (
    LOGGING_DIR,
    ROOT_DIR,
    get_dirs_to_initialize,
)
from odp_platform.common.string_utils import format_table_row, format_table_separator

LINE_WIDTH = 60
logger = logging.getLogger(__name__)


def initialize_project() -> None:
    """
    初始化项目，创建所有必要的目录。"""
    get_logger(
        base_path=LOGGING_DIR,
        log_type="init_project",
        temp_log=False,
    )

    logger.info("开始初始化项目核心目录".center(LINE_WIDTH, "="))
    logger.info(f"项目的根目录: {ROOT_DIR}")

    created: list[Path] = []
    existed: list[Path] = []

    for d in get_dirs_to_initialize():
        rel = d.relative_to(ROOT_DIR)
        if d.exists():
            logger.info(f"目录已经存在: {rel}")
            existed.append(d)
        else:
            try:
                d.mkdir(parents=True)
                logger.info(f"成功创建目录: {rel}")
                created.append(d)
            except OSError as e:
                logger.error(f"创建失败: {rel}: {e}")
                raise SystemExit(1) from e

    logger.info("项目核心目录初始化完成".center(LINE_WIDTH, "="))
    widths = [30, 12]
    aligns = ["left", "right"]
    logger.info(format_table_row(["目录", "状态"], widths, aligns))
    logger.info(format_table_separator(widths))

    for d in created:
        logger.info(format_table_row([str(d.relative_to(ROOT_DIR)), "新建"], widths, aligns))
    for d in existed:
        logger.info(format_table_row([d.relative_to(ROOT_DIR), "已存在"], widths, aligns))

    logger.info("=" * LINE_WIDTH)


if __name__ == "__main__":
    initialize_project()
