# ODPlatform - Core Engine

目标检测核心引擎，提供数据处理和 CLI 工具。

## 安装

```bash
pip install -e .
```

## 模块说明

| 模块 | 功能 |
|------|------|
| `odp_platform.common` | 基础工具（路径、日志、字符串工具） |
| `odp_platform.data_pipeline` | 数据管道（Pascal VOC / COCO / YOLO 格式转换） |
| `odp_platform.cli` | 命令行入口（odp-init, odp-reset, odp-transform） |

## CLI 命令

### 数据格式转换

```bash
odp-transform --format pascal_voc --input-dir /path/to/annotations --output-dir /path/to/output
odp-transform --format coco --input-dir /path/to/json --output-dir /path/to/output
odp-transform --format yolo --input-dir /path/to/txt --output-dir /path/to/output --classes person car dog
```

### 项目初始化

```bash
odp-init
```

### 项目重置

```bash
odp-reset
```

## 编程接口

```python
from odp_platform.data_pipeline import converter_data_to_yolo, ConvertOptions

classes = converter_data_to_yolo(
    input_dir="/path/to/annotations",
    output_labels_dir="/path/to/output",
    annotation_format="pascal_voc",
    options=ConvertOptions(),
)
print(classes)
```