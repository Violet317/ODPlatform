# Shared Datasets

## VisDrone2019-DET (当前使用)

### Source
VisDrone2019-DET dataset for object detection in aerial imagery.
Original VOC format stored in `raw/visdrone/`, converted YOLO format in `yolo/visdrone/`.

### Structure
```
raw/visdrone/
├── VisDrone2019-DET-train/     (6471 images + annotations, VOC 格式)
├── VisDrone2019-DET-val/       (548 images + annotations)
└── VisDrone2019-DET-test-dev/  (1610 images + annotations)

yolo/visdrone/                  (YOLO 格式，由 visdrone_to_yolo.py 生成)
├── data.yaml                   (数据集配置，相对路径兼容 Windows/WSL/Linux)
├── train/images/ + labels/     (6253 images)
└── val/images/ + labels/       (535 images)
```

### Classes (10)
`pedestrian`, `people`, `bicycle`, `car`, `van`, `truck`, `tricycle`, `awning-tricycle`, `bus`, `motor`

### Usage
```bash
# 转换 VOC → YOLO
python scripts/visdrone_to_yolo.py

# 训练
odp-train --model data/models/pretrained/yolo11n.pt --data data/yolo/visdrone/data.yaml
```

---

## RSOD Dataset (保留)

### Source
RSOD (Remote Sensing Object Detection) dataset.
- `RSOD/raw/`: Original VOC format annotations
- `RSOD/yolo/`: Converted YOLO format for training

### Classes
`aircraft`, `oiltank`, `overpass`, `playground`