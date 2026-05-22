from odp_platform.run_config.registry import register_field
from odp_platform.run_config.schema import ConfigField

SOURCE = register_field(ConfigField(
    name="source",
    type=str,
    default="",
    description="推理图像来源（路径或摄像头 ID）",
    group="predict_输入",
    examples=("data/test/images", "0", "path/to/video.mp4"),
    advice=("摄像头用 '0' 表示第一个摄像头",),
))

SAVE_TXT = register_field(ConfigField(
    name="save_txt",
    type=bool,
    default=False,
    description="是否保存结果为 TXT 标签",
    group="predict_输出",
    examples=("true", "false"),
))

SAVE_CONF = register_field(ConfigField(
    name="save_conf",
    type=bool,
    default=False,
    description="保存结果时是否包含置信度",
    group="predict_输出",
    examples=("true", "false"),
))

SAVE_CROP = register_field(ConfigField(
    name="save_crop",
    type=bool,
    default=False,
    description="是否裁剪并保存每个检测目标",
    group="predict_输出",
    examples=("true", "false"),
))

SHOW_LABELS = register_field(ConfigField(
    name="show_labels",
    type=bool,
    default=True,
    description="结果图像上是否显示标签",
    group="predict_展示",
    examples=("true", "false"),
))

SHOW_CONF = register_field(ConfigField(
    name="show_conf",
    type=bool,
    default=True,
    description="结果图像上是否显示置信度",
    group="predict_展示",
    examples=("true", "false"),
))

MAX_DET_PRED = register_field(ConfigField(
    name="max_det",
    type=int,
    default=300,
    description="单张图像最大检测框数",
    group="predict_后处理",
    ge=1,
    examples=("100", "300", "1000"),
))

DEVICE_PRED = register_field(ConfigField(
    name="device",
    type=str,
    default="cpu",
    description="推理设备",
    group="predict_输入",
    choices=("cpu", "0", "0,1", "mps"),
    examples=("cpu", "0"),
))