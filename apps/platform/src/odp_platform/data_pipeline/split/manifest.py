from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# 类型别名: 一对样本 = (image_path, label_path)
Pair = Tuple[Path, Path]
PairList = List[Pair]

# 支持的图片扩展名
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
# 对应的标签扩展名
LABEL_EXTENSION = ".txt"


@dataclass
class SplitManifest:
    """划分结果的数据载体。"""
    train: PairList = field(default_factory=list)
    val: PairList = field(default_factory=list)
    test: PairList = field(default_factory=list)

    train_rate: float = 0.0
    val_rate: float = 0.0
    test_rate: float = 0.0
    random_state: int = 0

    def summary(self) -> dict:
        return {
            "train": len(self.train),
            "val": len(self.val),
            "test": len(self.test),
            "total": len(self.train) + len(self.val) + len(self.test),
        }


def build_manifest(
    images_dir: Path,
    labels_dir: Path,
) -> List[Pair]:
    """构建 (图片路径, 标签路径) 配对清单。

    通过 basename (不含扩展名) 匹配图片和标签文件。

    Raises:
        FileNotFoundError: images_dir 或 labels_dir 不存在
        ValueError: 存在图片找不到对应标签 / 标签找不到对应图片
    """
    if not images_dir.is_dir():
        raise FileNotFoundError(f"图片目录不存在: {images_dir}")
    if not labels_dir.is_dir():
        raise FileNotFoundError(f"标签目录不存在: {labels_dir}")

    image_map: dict[str, Path] = {}
    for img in images_dir.iterdir():
        if img.suffix.lower() in IMAGE_EXTENSIONS:
            image_map[img.stem] = img

    label_map: dict[str, Path] = {}
    for lbl in labels_dir.glob(f"*{LABEL_EXTENSION}"):
        label_map[lbl.stem] = lbl

    if not image_map:
        raise FileNotFoundError(f"在 {images_dir} 下未找到图片文件")
    if not label_map:
        raise FileNotFoundError(f"在 {labels_dir} 下未找到标签文件")

    image_stems = set(image_map)
    label_stems = set(label_map)

    missing_labels = image_stems - label_stems
    missing_images = label_stems - image_stems

    if missing_labels:
        logger.warning(f"{len(missing_labels)} 张图缺少标签: {sorted(missing_labels)[:10]}")
    if missing_images:
        logger.warning(f"{len(missing_images)} 个标签缺少图片: {sorted(missing_images)[:10]}")

    common = sorted(image_stems & label_stems)
    if not common:
        raise ValueError(
            f"图片与标签无任何交集 (images_dir={images_dir}, labels_dir={labels_dir})"
        )

    result = [(image_map[stem], label_map[stem]) for stem in common]
    logger.info(f"配对成功: {len(result)} 对 (共 {len(image_map)} 图 / {len(label_map)} 标签)")
    return result