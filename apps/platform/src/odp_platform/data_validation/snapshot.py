from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from odp_platform.common.constants import IMAGE_EXTENSIONS, YOLO_LABEL_EXT
from odp_platform.common.paths import RAW_DATA_DIR, ROOT_DIR

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SplitStats:
    image_count: int
    annotated_count: int
    total_instances: int


@dataclass(frozen=True)
class DatasetSnapshot:
    yaml_path: Path
    yaml_data: Dict[str, Any]
    yaml_load_error: Optional[str]
    data_root: Path
    nc: Optional[int]
    class_names: Tuple[str, ...]
    task_type: str
    images_per_split: Dict[str, Tuple[Path, ...]]
    labels_per_split: Dict[str, Tuple[Path, ...]]
    stats_per_split: Dict[str, SplitStats]
    scan_warnings: Tuple[str, ...]

    @property
    def splits(self) -> Tuple[str, ...]:
        order = ["train", "val", "test"]
        return tuple(s for s in order if s in self.images_per_split)

    @property
    def total_images(self) -> int:
        return sum(len(paths) for paths in self.images_per_split.values())


def _list_images(directory: Path) -> List[Path]:
    result: List[Path] = []
    if not directory.is_dir():
        return result
    for ext in IMAGE_EXTENSIONS:
        result.extend(directory.glob(f"*{ext}"))
        result.extend(directory.glob(f"*{ext.upper()}"))
    return sorted(set(result))


def _list_labels(directory: Path) -> List[Path]:
    if not directory.is_dir():
        return []
    return sorted(directory.glob(f"*{YOLO_LABEL_EXT}"))


def _scan_split(
    yaml_data: Dict[str, Any],
    split_name: str,
    data_root: Path,
) -> Tuple[List[Path], List[Path], SplitStats]:
    rel_path = yaml_data.get(split_name)
    if not rel_path:
        return [], [], SplitStats(0, 0, 0)

    split_dir = Path(rel_path)
    if not split_dir.is_absolute():
        split_dir = data_root / split_dir

    # YOLO yaml 中 train/val/test 的值可能直接是 path（如 "train/images"），
    # 也可能是 path 的父目录（如 "train"）— 兼容两种写法
    images_dir = split_dir if split_dir.name == "images" else split_dir / "images"
    labels_dir = split_dir.parent / "labels" if split_dir.name == "images" else split_dir / "labels"

    images = _list_images(images_dir)
    labels = _list_labels(labels_dir)

    annotated = 0
    total_instances = 0
    for label_path in labels:
        try:
            lines = [l.strip() for l in label_path.read_text(encoding="utf-8").splitlines() if l.strip()]
            if lines:
                annotated += 1
                total_instances += len(lines)
        except Exception:
            pass

    return images, labels, SplitStats(len(images), annotated, total_instances)


def build_snapshot(
    yaml_path: Path,
    task_type: Optional[str] = None,
) -> DatasetSnapshot:
    yaml_data: Dict[str, Any] = {}
    yaml_load_error: Optional[str] = None
    scan_warnings: List[str] = []

    try:
        with open(yaml_path, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        yaml_load_error = f"yaml 文件不存在: {yaml_path}"
    except yaml.YAMLError as e:
        yaml_load_error = f"yaml 解析失败: {e}"

    if yaml_load_error:
        return DatasetSnapshot(
            yaml_path=yaml_path,
            yaml_data={},
            yaml_load_error=yaml_load_error,
            data_root=RAW_DATA_DIR,
            nc=None,
            class_names=(),
            task_type=task_type or "detect",
            images_per_split={},
            labels_per_split={},
            stats_per_split={},
            scan_warnings=(yaml_load_error,),
        )

    if not isinstance(yaml_data, dict):
        return DatasetSnapshot(
            yaml_path=yaml_path,
            yaml_data=yaml_data,
            yaml_load_error="yaml 顶层不是 dict",
            data_root=RAW_DATA_DIR,
            nc=None,
            class_names=(),
            task_type=task_type or "detect",
            images_per_split={},
            labels_per_split={},
            stats_per_split={},
            scan_warnings=("yaml 顶层不是 dict",),
        )

    nc = yaml_data.get("nc")
    if nc is not None and not isinstance(nc, int):
        scan_warnings.append(f"nc 字段类型非法: {type(nc).__name__}")
        nc = None

    names_raw = yaml_data.get("names", [])
    if isinstance(names_raw, dict):
        names = tuple(str(names_raw[k]) for k in sorted(names_raw) if k in names_raw)
    elif isinstance(names_raw, list):
        names = tuple(str(n) for n in names_raw)
    else:
        names = ()

    data_root = Path(yaml_data.get("path", RAW_DATA_DIR))
    if not data_root.is_absolute():
        data_root = (ROOT_DIR / data_root).resolve()

    resolved_task = yaml_data.get("task", task_type or "detect")

    images_per_split: Dict[str, Tuple[Path, ...]] = {}
    labels_per_split: Dict[str, Tuple[Path, ...]] = {}
    stats_per_split: Dict[str, SplitStats] = {}

    for split_name in ("train", "val", "test"):
        imgs, lbls, stats = _scan_split(yaml_data, split_name, data_root)
        images_per_split[split_name] = tuple(imgs)
        labels_per_split[split_name] = tuple(lbls)
        stats_per_split[split_name] = stats
        if not imgs and split_name in ("train", "val"):
            scan_warnings.append(f"split '{split_name}' 没有找到任何图像")

    return DatasetSnapshot(
        yaml_path=yaml_path,
        yaml_data=yaml_data,
        yaml_load_error=None,
        data_root=data_root,
        nc=nc,
        class_names=names,
        task_type=resolved_task,
        images_per_split=images_per_split,
        labels_per_split=labels_per_split,
        stats_per_split=stats_per_split,
        scan_warnings=tuple(scan_warnings),
    )