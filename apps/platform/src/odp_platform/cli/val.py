from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from odp_platform.common.logging_utils import get_logger
from odp_platform.common.paths import LOGGING_DIR
from odp_platform.evaluation import ValService

logger = logging.getLogger("odp-val")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odp-val",
        description=(
            "ODPlatform 模型评估命令 —— 使用 Ultralytics YOLO 验证模型精度。\n"
            "  1) 配置加载（支持 YAML/CLI 覆盖）\n"
            "  2) 模型推理验证\n"
            "  3) 结果保存到 runs/val/ 目录\n"
            "日志自动保存到 logging/val/ 目录，便于与评估结果对应。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--model", "-m", required=True,
                        help="模型路径（.pt 文件）或模型名称（如 yolo11n.pt）")

    # dataset 与 data 互为别名
    parser.add_argument("--dataset", "-d", dest="dataset", default=None,
                        help="数据集名（= configs/datasets/<name>.yaml）")
    parser.add_argument("--data", dest="dataset", default=None,
                        help="--dataset 的别名")

    parser.add_argument("--task", "-t", default="detect",
                        choices=("detect", "segment", "classify"),
                        help="算法任务类型 (默认 detect)")

    # yaml 与 config 互为别名
    parser.add_argument("--config", "-c", dest="yaml_path", default=None,
                        help="验证配置 YAML（不指定则自动生成）")
    parser.add_argument("--yaml", dest="yaml_path", default=None,
                        help="--config 的别名")

    parser.add_argument("--conf", type=float, default=None,
                        help="置信度阈值（覆盖配置中的值）")
    parser.add_argument("--iou", type=float, default=None,
                        help="NMS IoU 阈值（覆盖配置中的值）")
    parser.add_argument("--device", default=None,
                        help="验证设备（覆盖配置中的值，默认 cpu）")
    parser.add_argument("--batch", type=int, default=None,
                        help="验证批次大小（覆盖配置中的值）")
    parser.add_argument("--imgsz", type=int, default=None,
                        help="输入图像尺寸（覆盖配置中的值）")
    parser.add_argument("--half", type=bool, default=None,
                        help="半精度推理 FP16（覆盖配置中的值）")
    parser.add_argument("--max-det", type=int, default=None,
                        help="单张图像最大检测框数（覆盖配置中的值）")
    parser.add_argument("--name", default=None,
                        help="实验名称（默认自动生成，格式: val-{n}-{timestamp}-{model}）")
    parser.add_argument("--split", default="val",
                        choices=("train", "val", "test"),
                        help="验证数据集划分 (默认 val)")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅生成配置和参数预览，不实际验证")
    parser.add_argument("--save-json", action="store_true",
                        help="保存详细验证结果为 JSON")

    return parser


def _collect_cli_overrides(args) -> dict:
    overrides = {}
    for key in ("conf", "iou", "device", "batch", "imgsz", "max_det"):
        val = getattr(args, key, None)
        if val is not None:
            overrides[key] = val
    if args.half is not None:
        overrides["half"] = args.half
    return overrides


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    get_logger(base_path=LOGGING_DIR, log_type="val", log_level=logging.INFO,
               logger_name="odp-val")

    dataset = args.dataset
    if not dataset:
        logger.error("请指定数据集: --dataset <name> 或 --data <name>")
        logger.error("例如: odp-val --model best.pt --data rsod")
        return 2

    service = ValService()
    result = service.validate(
        model_path=args.model,
        dataset=dataset,
        yaml_path=args.yaml_path,
        task=args.task,
        split=args.split,
        cli_overrides=_collect_cli_overrides(args),
        name=args.name,
        dry_run=args.dry_run,
        save_json=args.save_json,
    )

    if not result.success:
        logger.error(f"评估失败: {result.error}")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())