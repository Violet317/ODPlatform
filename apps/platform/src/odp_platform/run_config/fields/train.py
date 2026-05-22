from odp_platform.run_config.registry import register_field
from odp_platform.run_config.schema import ConfigField

EPOCHS = register_field(ConfigField(
    name="epochs",
    type=int,
    default=100,
    description="训练总轮数",
    group="train_训练",
    ge=1,
    le=10000,
    examples=("50", "100", "300"),
    advice=("检测任务一般 100-300 轮收敛", "小数据集适当减少轮数"),
))

BATCH = register_field(ConfigField(
    name="batch",
    type=int,
    default=16,
    description="批次大小",
    group="train_训练",
    ge=1,
    le=1024,
    examples=("8", "16", "32", "64"),
    advice=("显存不足时调小，建议 2 的幂",),
))

LR0 = register_field(ConfigField(
    name="lr0",
    type=float,
    default=0.01,
    description="初始学习率",
    group="train_优化器",
    ge=1e-6,
    le=1.0,
    examples=("0.01", "0.001", "0.0001"),
    advice=("LR Finder 建议值附近微调", "过大导致不收敛，过小收敛慢"),
))

LRF = register_field(ConfigField(
    name="lrf",
    type=float,
    default=0.01,
    description="最终学习率 = lr0 * lrf",
    group="train_优化器",
    ge=0.0,
    le=1.0,
    examples=("0.01", "0.1", "0.001"),
    advice=("余弦退火策略的终点比例",),
))

MOMENTUM = register_field(ConfigField(
    name="momentum",
    type=float,
    default=0.937,
    description="SGD 动量 / Adam beta1",
    group="train_优化器",
    ge=0.0,
    le=1.0,
    examples=("0.9", "0.937", "0.95"),
))

WEIGHT_DECAY = register_field(ConfigField(
    name="weight_decay",
    type=float,
    default=0.0005,
    description="权重衰减（L2 正则化）",
    group="train_优化器",
    ge=0.0,
    le=1.0,
    examples=("0.0", "0.0005", "0.001"),
))

WARMUP_EPOCHS = register_field(ConfigField(
    name="warmup_epochs",
    type=float,
    default=3.0,
    description="热身轮数",
    group="train_训练",
    ge=0.0,
    le=50.0,
    examples=("0.0", "3.0", "5.0"),
    advice=("热身阶段学习率从低到高，有助于稳定初期训练",),
))

IMSZ = register_field(ConfigField(
    name="imgsz",
    type=int,
    default=640,
    description="输入图像尺寸（像素，正方形）",
    group="train_数据增强",
    ge=32,
    le=4096,
    examples=("416", "512", "640", "1280"),
    advice=("YOLO11n 默认 640", "大图增加显存占用但提升小目标性能"),
))

SAVE = register_field(ConfigField(
    name="save",
    type=bool,
    default=True,
    description="是否保存训练检查点",
    group="train_训练",
    examples=("true", "false"),
))

SAVE_PERIOD = register_field(ConfigField(
    name="save_period",
    type=int,
    default=-1,
    description="每隔 N 轮保存一次检查点（-1 表示仅保存最后一轮）",
    group="train_训练",
    ge=-1,
    examples=("-1", "5", "10"),
    advice=("配合 save=true 使用", "频繁保存增加磁盘 IO"),
))

VAL = register_field(ConfigField(
    name="val",
    type=bool,
    default=True,
    description="训练期间是否在验证集上评估",
    group="train_训练",
    examples=("true", "false"),
))

PATIENCE = register_field(ConfigField(
    name="patience",
    type=int,
    default=50,
    description="早停耐心值（连续 N 轮无提升则停止）",
    group="train_训练",
    ge=0,
    examples=("0", "50", "100"),
    advice=("0 表示禁用早停",),
))

AMP = register_field(ConfigField(
    name="amp",
    type=bool,
    default=True,
    description="自动混合精度训练",
    group="train_训练",
    examples=("true", "false"),
    advice=("开启后可加速并减少显存，NVIDIA GPU 推荐开启",),
))

FRACTION = register_field(ConfigField(
    name="fraction",
    type=float,
    default=1.0,
    description="使用数据集的百分比（用于快速实验）",
    group="train_数据",
    ge=0.01,
    le=1.0,
    examples=("1.0", "0.5", "0.1"),
    advice=("快速调试时设为 0.1，正式训练设为 1.0",),
))