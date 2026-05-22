from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from odp_platform.common.constants import DETAILS_PREVIEW_LIMIT
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check


@check("split_uniqueness")
def check_split_uniqueness(ctx: CheckContext) -> CheckResult:
    snapshot = ctx.snapshot
    if snapshot is None or snapshot.yaml_load_error:
        return CheckResult(
            name="split_uniqueness",
            severity=CheckSeverity.INFO,
            summary="snapshot 不可用, 跳过 split_uniqueness 检查",
            details={"reason": "snapshot_not_available"},
        )

    splits = snapshot.splits
    if len(splits) < 2:
        return CheckResult(
            name="split_uniqueness",
            severity=CheckSeverity.PASS,
            summary=f"只有一个 split ({splits[0] if splits else 'none'}), 无需判重",
            details={"splits": list(splits), "total_duplicates": 0, "overlaps": {}},
        )

    stem_map: Dict[str, str] = {}
    overlaps: Dict[str, Dict[str, List[str]]] = {}

    for split_name in splits:
        images = snapshot.images_per_split.get(split_name, ())
        for img in images:
            stem = img.stem
            if stem in stem_map:
                prev_split = stem_map[stem]
                if prev_split not in overlaps:
                    overlaps[prev_split] = {}
                if split_name not in overlaps[prev_split]:
                    overlaps[prev_split][split_name] = []
                if len(overlaps[prev_split][split_name]) < DETAILS_PREVIEW_LIMIT:
                    overlaps[prev_split][split_name].append(stem)
            else:
                stem_map[stem] = split_name

    total_duplicates = sum(
        len(stems) for pair in overlaps.values() for stems in pair.values()
    )

    if total_duplicates == 0:
        return CheckResult(
            name="split_uniqueness",
            severity=CheckSeverity.PASS,
            summary="各 split 之间无重复图像",
            details={"splits": list(splits), "total_duplicates": 0, "overlaps": {}},
        )

    return CheckResult(
        name="split_uniqueness",
        severity=CheckSeverity.ERROR,
        summary=f"发现 {total_duplicates} 个图像在多个 split 中重复（数据泄露）",
        details={
            "splits": list(splits),
            "total_duplicates": total_duplicates,
            "overlaps": overlaps,
        },
    )