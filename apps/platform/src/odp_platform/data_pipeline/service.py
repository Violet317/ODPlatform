#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :service.py
# @Time      :2026/5/19
# @Author    :MuU
# @Project   :ODPlatform

from __future__ import annotations

from pathlib import Path
from typing import List

from odp_platform.data_pipeline.registry import ConvertOptions, get_converter


def converter_data_to_yolo(
    input_dir: Path,
    output_labels_dir: Path,
    annotation_format: str,
    options: ConvertOptions,
) -> List[str]:
    entry = get_converter(annotation_format)
    if not entry.supports(options.task):
        raise ValueError(
            f"格式: {annotation_format!r} "
            f"不支持 task = {options.task!r} "
            f"支持的格式: {entry.supported_tasks}"
        )
    return entry.func(input_dir, output_labels_dir, options)