"""YOLO 直通 converter (接口等价性): 验证 + 硬链接/复制。

设计要点:
    - YOLO 已是目标格式, 无需"转换", 但仍要"输出"到 output_labels_dir
      ——让上层调用方看到所有 converter 行为一致 (接口等价)
    - 优先硬链接 (零空间, 零 IO), 失败降级到 copy
    - 顺道验证 txt 合法性: 列数、class_id 范围、坐标范围
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import List

from odp_platform.common.constants import AnnotationFormat, Task
from odp_platform.data_pipeline.registry import ConvertOptions, register

logger = logging.getLogger(__name__)


@register(AnnotationFormat.YOLO, supported_tasks=(Task.DETECT, Task.SEGMENT))
def passthrough_yolo(
    input_dir: Path,
    output_labels_dir: Path,
    options: ConvertOptions,
) -> List[str]:
    """直通: 验证 input_dir 是合法的 YOLO 目录, 硬链接/复制到 output。"""
    if options.classes is None or len(options.classes) == 0:
        raise ValueError(
            "YOLO 格式不包含类别名信息, 必须通过 options.classes 显式提供"
        )

    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(
            f"YOLO 直通: 在 {input_dir} 下未找到任何 .txt"
        )

    logger.info(
        f"YOLO 直通: 在 {input_dir} 中找到 {len(txt_files)} 个标签"
    )

    n_classes = len(options.classes)
    invalid = 0
    for txt in txt_files:
        if not _validate_yolo_txt(txt, n_classes):
            invalid += 1
    if invalid:
        logger.warning(
            f"YOLO 直通: {invalid} 个 txt 含非法行 (debug 日志记录详情)"
        )

    output_labels_dir.mkdir(parents=True, exist_ok=True)
    use_hardlink = _supports_hardlink(input_dir, output_labels_dir)
    method = "hardlink" if use_hardlink else "copy"
    logger.debug(f"YOLO 直通: 使用 {method} → {output_labels_dir}")

    for txt in txt_files:
        dst = output_labels_dir / txt.name
        if dst.exists():
            dst.unlink()
        if use_hardlink:
            try:
                os.link(txt, dst)
                continue
            except OSError:
                pass
        shutil.copy2(txt, dst)

    return list(options.classes)


def _validate_yolo_txt(txt: Path, n_classes: int) -> bool:
    """每行: 'cls_id cx cy w h', cls_id ∈ [0, n_classes), 其余 ∈ [0, 1]。"""
    try:
        text = txt.read_text(encoding="utf-8")
    except Exception as e:
        logger.debug(f"{txt.name} 读取失败: {e}")
        return False

    for ln_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            logger.debug(f"{txt.name}:{ln_no} 列数不为 5")
            return False
        try:
            cls = int(parts[0])
            coords = [float(x) for x in parts[1:]]
        except ValueError:
            return False
        if not (0 <= cls < n_classes):
            logger.debug(f"{txt.name}:{ln_no} class_id={cls} 越界")
            return False
        if not all(0.0 <= v <= 1.0 for v in coords):
            return False
    return True


def _supports_hardlink(src_dir: Path, dst_dir: Path) -> bool:
    """探测两个目录是否在同一文件系统 (硬链接的必要条件)。"""
    try:
        return src_dir.stat().st_dev == dst_dir.stat().st_dev
    except OSError:
        return False