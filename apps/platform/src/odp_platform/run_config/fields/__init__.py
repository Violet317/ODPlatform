from odp_platform.run_config.registry import register_field
from odp_platform.run_config.schema import ConfigField

TASK = register_field(ConfigField(
    name="task",
    type=str,
    default="train",
    description="运行任务类型（训练 / 验证 / 推理）",
    group="基础",
    choices=("train", "val", "predict"),
    examples=("train", "val", "predict"),
    advice=("训练选 train，验证选 val，推理选 predict",),
))

EXPERIMENT_NAME = register_field(ConfigField(
    name="experiment_name",
    type=str,
    default="",
    description="实验标识，用于区分本次运行的输出目录，不影响任务逻辑",
    group="基础",
    examples=("exp001", "lr-test", ""),
    advice=("留空则自动生成时间戳名称",),
))

MODEL = register_field(ConfigField(
    name="model",
    type=str,
    default="yolo11n.pt",
    description="模型名称或权重路径",
    group="模型",
    examples=("yolo11n.pt", "yolo11s.pt", "runs/train/exp/weights/best.pt"),
    advice=("轻量选 yolo11n.pt，精度优先选 yolo11x.pt",),
))

DEVICE = register_field(ConfigField(
    name="device",
    type=str,
    default="cpu",
    description="训练/推理设备",
    group="模型",
    choices=("cpu", "0", "0,1", "mps"),
    examples=("cpu", "0", "0,1"),
    advice=("单 GPU 写 '0'，多 GPU 写 '0,1'，CPU 写 'cpu'",),
))

WORKERS = register_field(ConfigField(
    name="workers",
    type=int,
    default=8,
    description="数据加载线程数",
    group="数据",
    ge=0,
    le=128,
    examples=("4", "8", "16"),
    advice=("Windows 建议 ≤ 8，Linux 可适当增大",),
))

SEED = register_field(ConfigField(
    name="seed",
    type=int,
    default=1210,
    description="随机种子，用于结果复现",
    group="数据",
    ge=0,
    examples=("42", "1210", "2024"),
    advice=("固定种子可保证每次运行的数据划分一致",),
))

VERBOSE = register_field(ConfigField(
    name="verbose",
    type=bool,
    default=True,
    description="是否输出详细日志",
    group="基础",
    examples=("true", "false"),
))