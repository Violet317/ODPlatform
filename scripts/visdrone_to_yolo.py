"""VisDrone2019-DET → YOLO 格式转换脚本

VisDrone 标注格式 (每行):
    <x1>,<y1>,<w>,<h>,<score>,<truncation>,<occlusion>,<class_id>
    - x1,y1,w,h: 左上角坐标和宽高 (像素)
    - class_id: 1~10, 0=忽略区域
    - score: 对 ground truth 通常为 0 或 1

YOLO 标注格式 (每行):
    <class_id> <x_center_norm> <y_center_norm> <width_norm> <height_norm>

用法:
    python scripts/visdrone_to_yolo.py
"""

import os
import shutil
from pathlib import Path

# VisDrone 类别名 (1-indexed)
VISDRONE_CLASSES = [
    "pedestrian",    # 1
    "people",        # 2
    "bicycle",       # 3
    "car",           # 4
    "van",           # 5
    "truck",         # 6
    "tricycle",      # 7
    "awning-tricycle",  # 8
    "bus",           # 9
    "motor",         # 10
]

RAW_DIR = Path("data/raw/visdrone")
YOLO_DIR = Path("data/yolo/visdrone")

SPLITS = {
    "train": RAW_DIR / "VisDrone2019-DET-train",
    "val":   RAW_DIR / "VisDrone2019-DET-val",
}


def get_image_size(img_path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
        with Image.open(img_path) as img:
            return img.size  # (width, height)
    except Exception:
        # 兜底: VisDrone 图片几乎都是 1920x1080
        return (1920, 1080)


def convert_annotation(txt_path: Path, img_w: int, img_h: int) -> list[str]:
    yolo_lines = []
    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 8:
                continue
            x1, y1, w, h = map(float, parts[:4])
            cls_id = int(parts[7])
            if cls_id == 0:
                continue  # 忽略区域
            # VisDrone class 1-indexed → YOLO 0-indexed
            cls_id -= 1
            if cls_id < 0 or cls_id >= len(VISDRONE_CLASSES):
                continue
            # 左上角 → 中心点
            cx = (x1 + w / 2) / img_w
            cy = (y1 + h / 2) / img_h
            nw = w / img_w
            nh = h / img_h
            yolo_lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
    return yolo_lines


def convert_split(split_name: str):
    src_dir = SPLITS[split_name]
    if not src_dir.exists():
        print(f"[SKIP] {src_dir} 不存在")
        return

    img_src = src_dir / "images"
    ann_src = src_dir / "annotations"
    if not img_src.exists() or not ann_src.exists():
        print(f"[SKIP] {src_dir} 缺少 images/ 或 annotations/ 子目录")
        return

    img_out = YOLO_DIR / split_name / "images"
    lbl_out = YOLO_DIR / split_name / "labels"
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(ann_src.glob("*.txt"))
    count = 0
    for txt_path in txt_files:
        stem = txt_path.stem
        img_path = img_src / f"{stem}.jpg"
        if not img_path.exists():
            continue

        img_w, img_h = get_image_size(img_path)
        yolo_lines = convert_annotation(txt_path, img_w, img_h)
        if not yolo_lines:
            continue

        # 写 YOLO 标注
        lbl_path = lbl_out / f"{stem}.txt"
        lbl_path.write_text("\n".join(yolo_lines) + "\n", encoding="utf-8")

        # 复制图片
        shutil.copy2(img_path, img_out / f"{stem}.jpg")
        count += 1

    print(f"[{split_name}] 转换完成: {count} 张图片 → {img_out}")


def main():
    print(f"VisDrone → YOLO 转换开始")
    print(f"  类别 ({len(VISDRONE_CLASSES)}): {', '.join(VISDRONE_CLASSES)}")
    print()

    for split in ["train", "val"]:
        convert_split(split)

    # 生成 data.yaml（使用相对路径，兼容 Windows / WSL / Linux）
    yaml_path = YOLO_DIR / "data.yaml"
    yaml_content = (
        f"# VisDrone2019-DET 数据集 (YOLO 格式)\n"
        f"train: train/images\n"
        f"val:   val/images\n"
        f"\nnc: {len(VISDRONE_CLASSES)}\n"
        f"names: {VISDRONE_CLASSES}\n"
    )
    yaml_path.write_text(yaml_content, encoding="utf-8")
    print(f"\n[data.yaml] 已生成: {yaml_path}")
    print(f"转换完成！YOLO 格式数据位于: {YOLO_DIR.resolve()}")


if __name__ == "__main__":
    main()