from __future__ import annotations

from typing import Any, Dict, List

from odp_platform.common.constants import (
    DETAILS_PREVIEW_LIMIT,
    PAIR_MISSING_ERROR_RATIO,
    PAIR_MISSING_WARN_RATIO,
    YOLO_LABEL_EXT,
)
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check


@check("pair_existence")
def check_pair_existence(ctx: CheckContext) -> CheckResult:
    snapshot = ctx.snapshot
    if snapshot is None or snapshot.yaml_load_error:
        return CheckResult(
            name="pair_existence",
            severity=CheckSeverity.INFO,
            summary="snapshot 不可用, 跳过 pair_existence 检查",
            details={"reason": "snapshot_not_available", "yaml_error": snapshot.yaml_load_error if snapshot else "snapshot_is_none"},
        )

    total_images = 0
    total_missing = 0
    missing_per_split: Dict[str, int] = {}
    missing_examples: Dict[str, List[str]] = {}

    for split_name in snapshot.splits:
        images = snapshot.images_per_split.get(split_name, ())
        labels = snapshot.labels_per_split.get(split_name, ())
        label_stems = {p.stem for p in labels}

        split_missing = 0
        split_examples: List[str] = []
        for img in images:
            total_images += 1
            if img.stem not in label_stems:
                split_missing += 1
                total_missing += 1
                if len(split_examples) < DETAILS_PREVIEW_LIMIT:
                    split_examples.append(img.name)

        if split_missing > 0:
            missing_per_split[split_name] = split_missing
            if split_examples:
                missing_examples[split_name] = split_examples

    missing_ratio = total_missing / total_images if total_images > 0 else 0.0

    if missing_ratio == 0.0:
        severity = CheckSeverity.PASS
        summary = "所有图像均有对应标签文件"
    elif missing_ratio < PAIR_MISSING_WARN_RATIO:
        severity = CheckSeverity.INFO
        summary = f"少量图像缺失标签: {total_missing}/{total_images} = {missing_ratio:.2%}"
    elif missing_ratio < PAIR_MISSING_ERROR_RATIO:
        severity = CheckSeverity.WARNING
        summary = f"较多图像缺失标签: {total_missing}/{total_images} = {missing_ratio:.2%}"
    else:
        severity = CheckSeverity.ERROR
        summary = f"大量图像缺失标签: {total_missing}/{total_images} = {missing_ratio:.2%}"

    details: Dict[str, Any] = {
        "total_images": total_images,
        "total_missing": total_missing,
        "missing_ratio": round(missing_ratio, 4),
        "thresholds": {
            "warn_ratio": PAIR_MISSING_WARN_RATIO,
            "error_ratio": PAIR_MISSING_ERROR_RATIO,
        },
        "missing_per_split": missing_per_split,
        "missing_examples": missing_examples,
    }

    return CheckResult(name="pair_existence", severity=severity, summary=summary, details=details)