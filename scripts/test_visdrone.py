"""验证 VisDrone YOLO 数据集 + Ultralytics 能正常加载（不做全量推理）"""
from pathlib import Path
import yaml

yaml_path = Path("data/yolo/visdrone/data.yaml")
data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
print(f"[yaml] nc={data['nc']}, names={data['names']}")

train_imgs = sorted(Path(data["train"]).glob("*.jpg"))
val_imgs = sorted(Path(data["val"]).glob("*.jpg"))
print(f"[train] {len(train_imgs)} images")
print(f"[val]   {len(val_imgs)} images")

train_lbls = sorted(Path("data/yolo/visdrone/train/labels").glob("*.txt"))
val_lbls = sorted(Path("data/yolo/visdrone/val/labels").glob("*.txt"))
print(f"[train] {len(train_lbls)} labels")
print(f"[val]   {len(val_lbls)} labels")

# 验证标注格式
sample_label = train_lbls[0]
lines = sample_label.read_text().strip().split("\n")
print(f"[sample] {sample_label.name}: {len(lines)} objects")
for l in lines[:3]:
    parts = l.strip().split()
    cls_id, cx, cy, w, h = map(float, parts)
    assert 0 <= cls_id <= 9, f"class_id 越界: {cls_id}"
    assert 0 <= cx <= 1, f"cx 越界: {cx}"
    assert 0 <= cy <= 1, f"cy 越界: {cy}"
    assert 0 <= w <= 1, f"w 越界: {w}"
    assert 0 <= h <= 1, f"h 越界: {h}"
    print(f"  cls={int(cls_id)}, cx={cx:.4f}, cy={cy:.4f}, w={w:.4f}, h={h:.4f}  [OK]")

# 验证 Ultralytics 能加载模型 + 解析数据集（不跑完整 val）
from ultralytics import YOLO, settings
model = YOLO("yolo11n.pt")
print(f"[model] yolo11n loaded (task={model.task})")

# 仅验证数据集能被 YOLO 解析
from ultralytics.data import YOLODataset
ds = YOLODataset(img_path=str(train_imgs[0].parent), data=data, task="detect")
print(f"[dataset] YOLODataset 创建成功，len={len(ds)} （所有图片）")

# 取 1 张图验证 data pipeline
sample = ds[0]
print(f"[sample_img] type={type(sample).__name__}, keys={list(sample.keys()) if isinstance(sample, dict) else 'N/A'}")
print("[OK] 数据集验证通过！可以在 GPU 上训练了")