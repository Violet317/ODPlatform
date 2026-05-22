"""创建测试数据集（Pascal VOC 格式）用于验证 D3/D4 流程。"""
from __future__ import annotations

from pathlib import Path
import shutil

src_images = Path(r"data\broken_voc\raw\images")
dst_root = Path(r"data\voc")
raw_dir = dst_root / "raw"
img_dir = raw_dir / "images"
ann_dir = raw_dir / "annotations"
img_dir.mkdir(parents=True, exist_ok=True)
ann_dir.mkdir(parents=True, exist_ok=True)

all_imgs = sorted(src_images.iterdir())
selected = all_imgs[:10]

cls_names = ["cat", "dog", "bird", "fish"]
width, height = 1920, 1080

for i, img in enumerate(selected):
    dst_img = img_dir / img.name
    shutil.copy2(img, dst_img)

    x = int(0.3 * width)
    y = int(0.4 * height)
    w = int(0.15 * width)
    h = int(0.15 * height)
    cls_id = i % 4

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<annotation>\n"
        "    <folder>images</folder>\n"
        f"    <filename>{img.name}</filename>\n"
        "    <size>\n"
        f"        <width>{width}</width>\n"
        f"        <height>{height}</height>\n"
        "        <depth>3</depth>\n"
        "    </size>\n"
        "    <object>\n"
        f"        <name>{cls_names[cls_id]}</name>\n"
        "        <bndbox>\n"
        f"            <xmin>{x}</xmin>\n"
        f"            <ymin>{y}</ymin>\n"
        f"            <xmax>{x + w}</xmax>\n"
        f"            <ymax>{y + h}</ymax>\n"
        "        </bndbox>\n"
        "    </object>\n"
        "</annotation>\n"
    )
    (ann_dir / img.with_suffix(".xml").name).write_text(xml, encoding="utf-8")

print(f"创建测试数据集: {raw_dir}")
print(f"  图像: {len(list(img_dir.iterdir()))} 个")
print(f"  标注: {len(list(ann_dir.iterdir()))} 个")