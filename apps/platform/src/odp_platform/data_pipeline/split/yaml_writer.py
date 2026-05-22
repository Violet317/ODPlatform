from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

from odp_platform.data_pipeline.split.manifest import SplitManifest

logger = logging.getLogger(__name__)


def write_dataset_yaml(
    yaml_path: Path,
    *,
    dataset_root: Path,
    classes: List[str],
    manifest: SplitManifest,
    dataset_name: str,
    source_format: str,
    task: str,
) -> None:
    """生成 ultralytics 兼容的 data.yaml, 含 odp_meta 块。

    Args:
        yaml_path: yaml 输出路径
        dataset_root: 数据集根目录 (用于 path 字段)
        classes: 类别名列表
        manifest: 划分结果 (含划分信息)
        dataset_name: 数据集名称
        source_format: 原始标注格式 (pascal_voc / coco / yolo)
        task: 任务类型 (detect / segment)
    """
    s = manifest.summary()
    doc = {
        "path": str(dataset_root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": len(classes),
        "names": {i: name for i, name in enumerate(classes)},
        "odp_meta": {
            "dataset": dataset_name,
            "source_format": source_format,
            "task": task,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "split": {
                "train_rate": round(manifest.train_rate, 6),
                "val_rate": round(manifest.val_rate, 6),
                "test_rate": round(manifest.test_rate, 6),
                "random_state": manifest.random_state,
                "counts": s,
            },
            "schema_version": 1,
        },
    }

    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)

    logger.info(f"YAML 已写入: {yaml_path} (nc={len(classes)})")