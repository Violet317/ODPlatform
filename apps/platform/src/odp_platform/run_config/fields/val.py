from odp_platform.run_config.registry import register_field
from odp_platform.run_config.schema import ConfigField

BATCH_VAL = register_field(ConfigField(
    name="batch",
    type=int,
    default=16,
    description="验证批次大小",
    group="val_验证",
    ge=1,
    le=1024,
    examples=("8", "16", "32"),
))

IMSZ_VAL = register_field(ConfigField(
    name="imgsz",
    type=int,
    default=640,
    description="验证输入尺寸",
    group="val_验证",
    ge=32,
    le=4096,
    examples=("416", "512", "640"),
))

CONF = register_field(ConfigField(
    name="conf",
    type=float,
    default=0.25,
    description="置信度阈值（仅验证+推理）",
    group="val_阈值",
    ge=0.0,
    le=1.0,
    examples=("0.25", "0.5", "0.75"),
    advice=("评估时一般保持默认 0.25",),
))

IOU = register_field(ConfigField(
    name="iou",
    type=float,
    default=0.7,
    description="NMS 的 IoU 阈值",
    group="val_阈值",
    ge=0.0,
    le=1.0,
    examples=("0.5", "0.7", "0.9"),
    advice=("值越低去重越严格，值越高重复框越多",),
))

MAX_DET = register_field(ConfigField(
    name="max_det",
    type=int,
    default=300,
    description="单张图像最大检测框数",
    group="val_阈值",
    ge=1,
    examples=("100", "300", "1000"),
))

HALF = register_field(ConfigField(
    name="half",
    type=bool,
    default=False,
    description="半精度推理（FP16）",
    group="val_验证",
    examples=("true", "false"),
    advice=("开启可加速，NVIDIA Tensor Core GPU 推荐",),
))

DEVICE_VAL = register_field(ConfigField(
    name="device",
    type=str,
    default="cpu",
    description="验证设备",
    group="val_验证",
    choices=("cpu", "0", "0,1", "mps"),
    examples=("cpu", "0"),
))