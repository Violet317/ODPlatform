from __future__ import annotations

from typing import Any, Dict, List, Tuple

from odp_platform.run_config.registry import field_names
from odp_platform.run_config.schema import TraceRecord, TraceReport

_SOURCE_DEFAULTS = "代码默认值"
SOURCE_YAML = "YAML 配置"
SOURCE_CLI = "命令行参数"


def merge(
    defaults: Dict[str, Any],
    yaml_config: Dict[str, Any],
    cli_args: Dict[str, Any],
    task: str,
) -> Tuple[Dict[str, Any], TraceReport]:
    known = set(field_names(task)) if task else set(field_names())
    all_keys = known | set(defaults) | set(yaml_config) | set(cli_args)

    merged: Dict[str, Any] = {}
    records: List[TraceRecord] = []

    for key in sorted(all_keys):
        default_val = defaults.get(key)
        yaml_val = yaml_config.get(key) if key in yaml_config else _MISSING
        cli_val = cli_args.get(key) if key in cli_args else _MISSING

        chain: List[Tuple[str, Any]] = [(_SOURCE_DEFAULTS, default_val)]

        final_val = default_val

        if yaml_val is not _MISSING:
            chain.append((SOURCE_YAML, yaml_val))
            final_val = yaml_val

        if cli_val is not _MISSING:
            chain.append((SOURCE_CLI, cli_val))
            final_val = cli_val

        merged[key] = final_val
        records.append(TraceRecord(
            field=key,
            final_value=final_val,
            sources=tuple(chain),
        ))

    return merged, TraceReport(records=tuple(records))


class _Missing:
    def __repr__(self):
        return "<MISSING>"


_MISSING = _Missing()