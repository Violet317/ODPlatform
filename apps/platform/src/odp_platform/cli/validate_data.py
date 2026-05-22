from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from odp_platform.common.logging_utils import get_logger
from odp_platform.common.paths import APP_DIR, LOGGING_DIR, ROOT_DIR, dataset_yaml_path
from odp_platform.data_validation import render_to_logger, validate_dataset

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="odp-validate",
        description="ODPlatform 数据质检工具 —— 检查数据集配置、标签完整性、格式合法性和 split 唯一性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--dataset", "-d", type=str, help="数据集名 (= configs/datasets/<name>.yaml)")
    source.add_argument("--yaml", type=str, dest="yaml_path", help="直接指定 yaml 文件路径（调试用）")

    parser.add_argument("--task", "-t", type=str, default=None, choices=["detect", "segment"],
                        help="任务类型 (默认从 yaml 读取, 兜底 detect)")
    parser.add_argument("--no-report", action="store_true", help="不写 JSON 报告")
    parser.add_argument("--verbose", "-v", action="store_true", help="DEBUG 级日志")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    cli_logger = get_logger(base_path=LOGGING_DIR, log_type="validate", log_level=log_level)

    try:
        if args.dataset:
            yaml_path = dataset_yaml_path(args.dataset)
        else:
            raw = Path(args.yaml_path)
            if raw.is_file():
                yaml_path = raw
            elif (ROOT_DIR / raw).is_file():
                yaml_path = ROOT_DIR / raw
            elif (APP_DIR / raw).is_file():
                yaml_path = APP_DIR / raw
            else:
                yaml_path = raw

        if not yaml_path.is_file():
            logger.error(f"YAML 文件不存在: {yaml_path}")
            return 2

        report = validate_dataset(
            yaml_path=yaml_path,
            task_type=args.task,
            write_report=not args.no_report,
        )

        render_to_logger(report, cli_logger, report_path=report.report_path)
        return report.exit_code

    except KeyboardInterrupt:
        cli_logger.warning("用户中断")
        return 3
    except Exception as e:
        cli_logger.exception(f"未预期异常: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
