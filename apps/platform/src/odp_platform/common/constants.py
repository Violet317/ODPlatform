#!/usr/bin/env python
# @FileName  :constants.py
# @Time      :2026/5/20
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :共享词汇表 —— 数据管线中用到的枚举、字面量、默认值

from __future__ import annotations

from typing import Final


class AnnotationFormat:
    """支持的标注格式（字符串常量，使装饰器可直接引用）。"""
    PASCAL_VOC = "pascal_voc"
    COCO = "coco"
    YOLO = "yolo"

    @classmethod
    def all(cls) -> tuple[str, ...]:
        return cls.PASCAL_VOC, cls.COCO, cls.YOLO


class Task:
    """算法任务类型（检测 / 分割）。"""
    DETECT = "detect"
    SEGMENT = "segment"

    @classmethod
    def all(cls) -> tuple[str, ...]:
        return cls.DETECT, cls.SEGMENT


class RunTask:
    """运行任务类型（训练 / 验证 / 推理）。"""
    TRAIN = "train"
    VAL = "val"
    PREDICT = "predict"

    @classmethod
    def all(cls) -> tuple[str, ...]:
        return cls.TRAIN, cls.VAL, cls.PREDICT


# 各格式支持的任务（映射表，与 Task 类配合使用）
FORMAT_CAPABILITIES: Final[dict[str, tuple[str, ...]]] = {
    AnnotationFormat.PASCAL_VOC: (Task.DETECT,),
    AnnotationFormat.COCO: (Task.DETECT, Task.SEGMENT),
    AnnotationFormat.YOLO: (Task.DETECT,),
}

# ============================================================
#  划分相关常量
# ============================================================

DEFAULT_RANDOM_STATE: Final[int] = 1210

# 浮点精度容差 —— 用于比率求和校验
# 1.0 - 0.7 - 0.3 在 IEEE 754 中不等于 0，需要用容差判断
RATE_EPSILON: float | int = 1e-6

# ============================================================
#  数据集覆盖率阈值
# ============================================================

# 图像-标注覆盖率硬阈值：低于此值直接 fail-fast
COVERAGE_HARD_THRESHOLD: float = 0.5
# 图像-标注覆盖率软阈值：低于此值仅警告
COVERAGE_SOFT_THRESHOLD: float = 0.9

# ============================================================
#  数据校验（D4）阈值
# ============================================================

# pair_existence check：缺失比例 ≥ 此值 → ERROR
PAIR_MISSING_ERROR_RATIO: float = 0.5
# pair_existence check：缺失比例 ≥ 此值 → WARNING
PAIR_MISSING_WARN_RATIO: float = 0.05

# 质检详情预览条数上限（防 JSON 报告爆炸）
DETAILS_PREVIEW_LIMIT: int = 20

# ============================================================
#  文件后缀 / 目录名
# ============================================================

IMAGE_EXTENSIONS: Final[tuple[str, ...]] = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

YOLO_LABEL_EXT: Final[str] = ".txt"

YOLO_IMAGES_DIRNAME: Final[str] = "images"
YOLO_LABELS_DIRNAME: Final[str] = "labels"

# ============================================================
#  YAML schema
# ============================================================

SCHEMA_VERSION: Final[int] = 1
