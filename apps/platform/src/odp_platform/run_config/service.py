from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from odp_platform.run_config.loader import load_yaml, parse_cli_args, resolve_yaml_path
from odp_platform.run_config.merger import merge
from odp_platform.run_config.registry import list_fields
from odp_platform.run_config.schema import ConfigBundle, ConfigSnapshot
from odp_platform.run_config.validator import validate_config


def restore_from_snapshot(
    snapshot: ConfigSnapshot,
    cli_args: Optional[Dict[str, Any]] = None,
) -> ConfigBundle:
    """从配置快照恢复完整配置（FR-23）。

    恢复时执行完整验证流程，在配置定义后续演进时能立即发现不兼容情况。
    """
    merged = dict(snapshot.config)

    parsed_cli = parse_cli_args(cli_args or {})

    from odp_platform.run_config.merger import _SOURCE_DEFAULTS, _MISSING, merge
    if parsed_cli:
        from odp_platform.run_config.registry import list_fields
        defaults = {name: f.default for name, f in list_fields(snapshot.task).items()}
        merged, trace = merge(defaults, {}, parsed_cli, snapshot.task)
        for key in parsed_cli:
            merged[key] = parsed_cli[key]
    else:
        from odp_platform.run_config.schema import TraceRecord, TraceReport
        from odp_platform.run_config.merger import _SOURCE_DEFAULTS
        records = []
        for key, val in snapshot.config.items():
            records.append(TraceRecord(
                field=key,
                final_value=val,
                sources=((_SOURCE_DEFAULTS, val),),
            ))
        trace = TraceReport(records=tuple(records))

    trace_map = {r.field: r for r in trace.records}
    errors, warnings = validate_config(merged, snapshot.task, trace_map)

    return ConfigBundle(
        task=snapshot.task,
        config=merged,
        trace=trace,
        errors=errors,
        warnings=warnings,
    )


def save_snapshot_to_file(snapshot: ConfigSnapshot, path: Path) -> str:
    """将配置快照保存为 JSON 文件。"""
    path.write_text(
        json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def load_snapshot_from_file(path: Path) -> ConfigSnapshot:
    """从 JSON 文件加载配置快照。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    return ConfigSnapshot.from_dict(data)


def build_config(
    task: str,
    yaml_path: Optional[Path] = None,
    cli_args: Optional[Dict[str, Any]] = None,
    preview_only: bool = False,
) -> ConfigBundle:
    fields = list_fields()
    defaults = {name: f.default for name, f in fields.items()}

    yaml_config: Dict[str, Any] = {}
    yaml_load_error: Optional[str] = None
    if yaml_path is not None:
        yaml_config, yaml_load_error = load_yaml(yaml_path)

    parsed_cli = parse_cli_args(cli_args or {})

    merged, trace = merge(defaults, yaml_config, parsed_cli, task)

    if yaml_load_error and not preview_only:
        from odp_platform.run_config.schema import ValidationError

        if "文件不存在" in yaml_load_error:
            cmd = f"odp-config generate --task {task} --output {yaml_path}"
            enhanced = (
                f"{yaml_load_error}\n"
                f"请先生成配置模板: {cmd}"
            )
        else:
            enhanced = yaml_load_error

        errors = [
            ValidationError(
                field="(yaml)",
                message=enhanced,
                current_value=str(yaml_path) if yaml_path else "",
            )
        ]
        return ConfigBundle(
            task=task,
            config=merged,
            trace=trace,
            errors=errors,
            warnings=[],
        )

    if preview_only:
        return ConfigBundle(
            task=task,
            config=merged,
            trace=trace,
            errors=[],
            warnings=[],
        )

    trace_map = {r.field: r for r in trace.records}
    errors, warnings = validate_config(merged, task, trace_map)

    return ConfigBundle(
        task=task,
        config=merged,
        trace=trace,
        errors=errors,
        warnings=warnings,
    )