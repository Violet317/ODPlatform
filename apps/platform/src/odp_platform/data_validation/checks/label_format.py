from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from odp_platform.common.constants import DETAILS_PREVIEW_LIMIT
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

ERROR_FIELD_COUNT_MISMATCH = "field_count_mismatch"
ERROR_PARSE = "parse_error"
ERROR_CLASS_ID = "class_id_out_of_range"
ERROR_COORD = "coord_out_of_range"
ERROR_POLYGON_POINTS = "polygon_too_few_points"


def _parse_label_line(line: str, line_no: int) -> Tuple[bool, List[float], str]:
    parts = line.strip().split()
    nums: List[float] = []
    for p in parts:
        try:
            nums.append(float(p))
        except ValueError:
            return False, [], ERROR_PARSE
    return True, nums, ""


def _validate_detect(nums: List[float], nc: int) -> List[str]:
    errors: List[str] = []
    if len(nums) != 5:
        return [ERROR_FIELD_COUNT_MISMATCH]
    cls_id = int(nums[0])
    if cls_id < 0 or cls_id >= nc:
        errors.append(ERROR_CLASS_ID)
    for coord in nums[1:]:
        if coord < 0.0 or coord > 1.0:
            errors.append(ERROR_COORD)
            break
    return errors


def _validate_segment(nums: List[float], nc: int) -> List[str]:
    errors: List[str] = []
    if len(nums) < 7 or (len(nums) - 1) % 2 != 0:
        return [ERROR_FIELD_COUNT_MISMATCH]
    cls_id = int(nums[0])
    if cls_id < 0 or cls_id >= nc:
        errors.append(ERROR_CLASS_ID)
    num_points = (len(nums) - 1) // 2
    if num_points < 3:
        errors.append(ERROR_POLYGON_POINTS)
    for coord in nums[1:]:
        if coord < 0.0 or coord > 1.0:
            errors.append(ERROR_COORD)
            break
    return errors


@check("label_format")
def check_label_format(ctx: CheckContext) -> CheckResult:
    snapshot = ctx.snapshot
    if snapshot is None or snapshot.yaml_load_error:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.INFO,
            summary="snapshot 不可用, 跳过 label_format 检查",
            details={"reason": "snapshot_not_available"},
        )

    if snapshot.nc is None or snapshot.nc <= 0:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.INFO,
            summary="nc 不可用或非法, 跳过 label_format 检查",
            details={"reason": "nc_unavailable", "nc": snapshot.nc},
        )

    task_type = snapshot.task_type
    nc = snapshot.nc
    total_lines = 0
    total_errors = 0
    error_kinds: Dict[str, int] = {}
    errors_preview: List[Dict[str, Any]] = []

    for split_name in snapshot.splits:
        label_paths = snapshot.labels_per_split.get(split_name, ())
        for label_path in label_paths:
            try:
                lines = label_path.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for line_no, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                total_lines += 1

                ok, nums, err = _parse_label_line(stripped, line_no)
                if not ok:
                    total_errors += 1
                    error_kinds[err] = error_kinds.get(err, 0) + 1
                    if len(errors_preview) < DETAILS_PREVIEW_LIMIT:
                        errors_preview.append({
                            "file": label_path.name,
                            "split": split_name,
                            "line": line_no,
                            "error_type": err,
                        })
                    continue

                if task_type == "segment":
                    line_errors = _validate_segment(nums, nc)
                else:
                    line_errors = _validate_detect(nums, nc)

                if line_errors:
                    total_errors += 1
                    for e in line_errors:
                        error_kinds[e] = error_kinds.get(e, 0) + 1
                    if len(errors_preview) < DETAILS_PREVIEW_LIMIT:
                        errors_preview.append({
                            "file": label_path.name,
                            "split": split_name,
                            "line": line_no,
                            "error_type": line_errors[0],
                        })

    if total_errors == 0:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.PASS,
            summary=f"标签格式校验通过 ({total_lines} 行)",
            details={"task_type": task_type, "total_lines": total_lines, "total_errors": 0, "error_kinds": {}, "errors_preview": []},
        )

    return CheckResult(
        name="label_format",
        severity=CheckSeverity.ERROR,
        summary=f"标签格式错误: {total_errors}/{total_lines} 行有问题",
        details={
            "task_type": task_type,
            "total_lines": total_lines,
            "total_errors": total_errors,
            "error_kinds": error_kinds,
            "errors_preview": errors_preview,
        },
    )