"""解压 rsod.zip 并整理为 Pascal VOC 格式"""
import zipfile
import shutil
from pathlib import Path

ZIP_PATH = Path("data/rsod.zip")
RAW_DIR = Path("data/RSOD/raw")

if not ZIP_PATH.exists():
    print(f"[ERROR] 找不到 {ZIP_PATH}")
    exit(1)

# 清理旧目录
if RAW_DIR.exists():
    shutil.rmtree(RAW_DIR)

# 解压到临时目录
TMP = Path("data/RSOD/_tmp")
if TMP.exists():
    shutil.rmtree(TMP)

print(f"正在解压 {ZIP_PATH} ...")
with zipfile.ZipFile(ZIP_PATH) as z:
    z.extractall(TMP)

# 整理为 VOC 格式: raw/train/{Annotations, JPEGImages}
ann_src = TMP / "rsod" / "annotations"
img_src = TMP / "rsod" / "images"

ann_dst = RAW_DIR / "train" / "Annotations"
img_dst = RAW_DIR / "train" / "JPEGImages"
ann_dst.mkdir(parents=True, exist_ok=True)
img_dst.mkdir(parents=True, exist_ok=True)

# 移动标注
for f in sorted(ann_src.glob("*.xml")):
    shutil.copy2(f, ann_dst / f.name)

# 移动图片
for f in sorted(img_src.glob("*.jpg")):
    shutil.copy2(f, img_dst / f.name)

# 清理临时目录
shutil.rmtree(TMP)

n_xml = len(list(ann_dst.glob("*.xml")))
n_jpg = len(list(img_dst.glob("*.jpg")))
print(f"VOC 格式已就绪:")
print(f"  {ann_dst}  ({n_xml} 个标注)")
print(f"  {img_dst}  ({n_jpg} 张图片)")
