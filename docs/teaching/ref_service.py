#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :service.py
# @Time      :2026/5/22 10:11:51
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :调度层,跑所有的测试
from __future__ import  annotations

import logging
from typing import List
import json
import time
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
from odp_platform.common.paths import validation_run_dir
from odp_platform.data_validation.report import ValidationReport
from odp_platform.data_validation.snapshot import build_snapshot

from odp_platform.common.perfirmance_utils import time_it
from odp_platform.data_validation.registry import (CheckContext, CheckEntry, CheckResult, CheckSeverity,get_all_checks)

logger = logging.getLogger(__name__)

def run_all_checks(ctx: CheckContext) -> List[CheckResult]:
    entries = get_all_checks()
    logger.info(f"开始执行 {len(entries)}个检测")

    results: List[CheckResult] = []
    for entry in entries:
        result = _safe_run_one(entry, ctx)
        _log_check_result(result)
        results.append(result)
    _log_summary(results)
    return results

def _safe_run_one(entry: CheckEntry, ctx: CheckContext) -> CheckResult:
    """
    跑单个check,异常包装城ERROR
    """
    try:
        return entry.func(ctx)
    except Exception as e:
        logger.exception(f"check {entry.name} 出现异常，已捕获为 ERROR 级结果")
        return  CheckResult(
            name=entry.name,
            severity=CheckSeverity.ERROR,
            summary=f"check 内部异常： {type(e).__name__}: {e}",
            details = {"exception_type": type(e).__name__,
                    "exception_msg": str(e)
                    }
        )


def _log_check_result(r: CheckResult) -> None:
    log_method = {
        CheckSeverity.ERROR : logger.error,
        CheckSeverity.WARNING: logger.warning,
        CheckSeverity.INFO: logger.info,
        CheckSeverity.PASS: logger.debug,
    }.get(r.severity, logger.info)

    log_method(f"[{r.severity:7s}] {r.name}: {r.summary}")


def _log_summary(results: List[CheckResult]) -> None:
    counts = {}
    for r in results:
        counts[r.severity] = counts.get(r.summary, 0) + 1
    parts = [f"{n} {s}" for s, n in counts.items()]
    logger.info(f"check执行完毕： {' / '.join(parts)}")




def validate_dataset(
    yaml_path:    Path,
    task_type:    Optional[str] = None,
    run_id:       Optional[str] = None,
    run_dir:      Optional[Path] = None,
    write_report: bool = True,
) -> ValidationReport:
    """端到端验证: 构造 snapshot → 跑 check → 包装 report → 可选写盘。

    Args:
        yaml_path:    数据集 yaml 文件路径
        task_type:    'detect' / 'segment' / None (None → 读 yaml.task, 再不行 detect)
        run_id:       手动指定运行 ID; None 表示自动用时间戳
        run_dir:      手动指定运行目录; None 表示用 validation_run_dir(run_id)
        write_report: 是否写 JSON 报告到 run_dir/report.json

    Returns:
        ValidationReport (run_dir 字段已填, 调用方可以拿 .report_path 取 JSON 位置)
    """
    # ---- 解析 run_id / run_dir ----
    resolved_run_id  = run_id  or datetime.now().strftime("%Y%m%d_%H%M%S")
    resolved_run_dir = run_dir or (validation_run_dir(resolved_run_id) if write_report else None)

    if write_report and resolved_run_dir is not None:
        resolved_run_dir.mkdir(parents=True, exist_ok=True)

    # ---- 跑核心流程 ----
    t0 = time.perf_counter()
    started_iso = datetime.now(timezone.utc).isoformat()

    snapshot = build_snapshot(yaml_path=yaml_path, task_type=task_type)
    ctx      = CheckContext(yaml_path=yaml_path, snapshot=snapshot)
    results  = run_all_checks(ctx)

    duration = time.perf_counter() - t0

    # ---- 包装 ValidationReport ----
    report = ValidationReport(
        run_id=resolved_run_id,
        yaml_path=yaml_path,
        snapshot=snapshot,
        results=results,
        duration_seconds=duration,
        started_at_iso=started_iso,
        run_dir=resolved_run_dir,
    )

    # ---- 写 JSON 报告 ----
    if write_report and resolved_run_dir is not None:
        report_path = resolved_run_dir / "report.json"
        report_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return report
