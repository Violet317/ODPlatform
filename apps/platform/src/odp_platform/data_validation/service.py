from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from odp_platform.common.paths import LOGGING_DIR, validation_run_dir
from odp_platform.common.performance_utils import time_it
from odp_platform.data_validation.registry import (
    CheckContext,
    CheckEntry,
    CheckResult,
    CheckSeverity,
    _lazy_init,
    _REGISTRY,
    get_check,
)
from odp_platform.data_validation.report import ValidationReport
from odp_platform.data_validation.snapshot import DatasetSnapshot, build_snapshot

logger = logging.getLogger(__name__)


def _safe_run_one(ctx: CheckContext, entry: CheckEntry) -> CheckResult:
    try:
        return entry.func(ctx)
    except Exception as e:
        logger.exception(f"Check '{entry.name}' 执行异常")
        return CheckResult(
            name=entry.name,
            severity=CheckSeverity.ERROR,
            summary=f"check 执行异常: {e}",
            details={"error": str(e), "exception_type": type(e).__name__},
        )


@time_it(name="run_all_checks")
def run_all_checks(ctx: CheckContext) -> List[CheckResult]:
    _lazy_init()
    results: List[CheckResult] = []
    for name in sorted(_REGISTRY.keys()):
        entry = get_check(name)
        result = _safe_run_one(ctx, entry)
        results.append(result)
    return results


def validate_dataset(
    yaml_path: Path,
    task_type: Optional[str] = None,
    run_id: Optional[str] = None,
    run_dir: Optional[Path] = None,
    write_report: bool = True,
) -> ValidationReport:
    from odp_platform.common.system_utils import log_device_info

    log_device_info(logger)

    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if run_dir is None:
        run_dir = validation_run_dir(run_id)
    if write_report:
        run_dir.mkdir(parents=True, exist_ok=True)

    started_at_iso = datetime.now(timezone.utc).isoformat()
    start_time = time.perf_counter()

    snapshot = build_snapshot(yaml_path, task_type=task_type)

    ctx = CheckContext(yaml_path=yaml_path, snapshot=snapshot)
    results = run_all_checks(ctx)

    duration_seconds = time.perf_counter() - start_time

    report = ValidationReport(
        run_id=run_id,
        yaml_path=yaml_path,
        snapshot=snapshot,
        results=results,
        duration_seconds=round(duration_seconds, 3),
        started_at_iso=started_at_iso,
        run_dir=run_dir if write_report else None,
    )

    if write_report:
        report_path = run_dir / "report.json"
        report_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"质检报告已写入: {report_path}")

    return report