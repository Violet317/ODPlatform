from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check


@check("yaml_schema")
def validate_yaml_schema(ctx: CheckContext) -> CheckResult:
    problems: List[str] = []

    yaml_path: Path = ctx.yaml_path
    yaml_data: Dict[str, Any] = {}
    yaml_load_error: str | None = None

    if not yaml_path.exists():
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml 文件不存在: {yaml_path}",
            details={"error": "file_not_found", "path": str(yaml_path)},
        )

    try:
        with open(yaml_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            return CheckResult(
                name="yaml_schema",
                severity=CheckSeverity.ERROR,
                summary="yaml 顶层不是 dict",
                details={"error": "not_a_dict", "type": type(raw).__name__},
            )
        yaml_data = raw
    except yaml.YAMLError as e:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml 解析失败: {e}",
            details={"error": "parse_error", "detail": str(e)},
        )

    nc = yaml_data.get("nc")
    if nc is None:
        problems.append("缺少 nc 字段")
    elif not isinstance(nc, int) or nc <= 0:
        problems.append(f"nc 应为正整数, 当前: {nc}")

    names = yaml_data.get("names")
    if names is None:
        problems.append("缺少 names 字段")
    else:
        names_valid = False
        if isinstance(names, list):
            names_valid = all(isinstance(n, str) and n.strip() for n in names)
        elif isinstance(names, dict):
            names_valid = all(
                isinstance(k, int) and isinstance(v, str) and v.strip()
                for k, v in names.items()
            )
        if not names_valid:
            problems.append("names 字段格式非法: 应为 list[str] 或 dict[int, str], 且元素非空")

    if isinstance(nc, int) and nc > 0 and names is not None:
        if isinstance(names, list) and len(names) != nc:
            problems.append(f"len(names)={len(names)} != nc={nc}")
        elif isinstance(names, dict) and len(names) != nc:
            problems.append(f"len(names)={len(names)} != nc={nc}")

    if problems:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml schema 校验失败: {'; '.join(problems)}",
            details={"problems": problems},
        )

    return CheckResult(
        name="yaml_schema",
        severity=CheckSeverity.PASS,
        summary="yaml schema 校验通过",
        details={"nc": nc, "class_count": len(names) if isinstance(names, (list, dict)) else 0},
    )