from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from odp_platform.run_config.registry import get_field, list_fields
from odp_platform.run_config.schema import (
    ConfigField,
    TraceRecord,
    ValidationError,
    ValidationWarning,
)


def validate_config(
    config: Dict[str, Any],
    task: str,
    trace_records: Optional[Dict[str, TraceRecord]] = None,
) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []

    fields = list_fields()
    known_names = set(fields)

    for key, value in config.items():
        if key not in known_names:
            errors.append(ValidationError(
                field=key,
                message=f"未知字段 '{key}'，不在 {task} 任务的配置定义中",
                current_value=value,
                trace=trace_records.get(key) if trace_records else None,
            ))
            continue

        field_def = fields[key]
        err = _validate_one(key, value, field_def, trace_records)
        if err:
            errors.append(err)

    cross_errors, cross_warnings = _validate_cross_field(config, fields, trace_records)
    errors.extend(cross_errors)
    warnings.extend(cross_warnings)

    return errors, warnings


def _validate_one(
    name: str,
    value: Any,
    field: ConfigField,
    trace_records: Optional[Dict[str, TraceRecord]] = None,
) -> Optional[ValidationError]:
    if value is None and field.default is None:
        return None

    if field.choices is not None and value not in field.choices:
        return ValidationError(
            field=name,
            message=f"取值 '{value}' 不在合法集合 {field.choices} 中",
            current_value=value,
            trace=trace_records.get(name) if trace_records else None,
        )

    if field.type == int:
        try:
            v = int(value)
        except (TypeError, ValueError):
            return ValidationError(
                field=name,
                message=f"值 {value!r} 无法转换为 int",
                current_value=value,
            )
        if field.ge is not None and v < field.ge:
            return ValidationError(
                field=name,
                message=f"值 {v} 小于最小值 {field.ge}",
                current_value=value,
            )
        if field.le is not None and v > field.le:
            return ValidationError(
                field=name,
                message=f"值 {v} 大于最大值 {field.le}",
                current_value=value,
            )

    elif field.type == float:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return ValidationError(
                field=name,
                message=f"值 {value!r} 无法转换为 float",
                current_value=value,
            )
        if field.ge is not None and v < field.ge:
            return ValidationError(
                field=name,
                message=f"值 {v} 小于最小值 {field.ge}",
                current_value=value,
            )
        if field.le is not None and v > field.le:
            return ValidationError(
                field=name,
                message=f"值 {v} 大于最大值 {field.le}",
                current_value=value,
            )

    elif field.type == bool:
        if not isinstance(value, bool):
            return ValidationError(
                field=name,
                message=f"值 {value!r} 不是布尔类型",
                current_value=value,
            )

    if field.validator is not None:
        msg = field.validator(value)
        if msg:
            return ValidationError(
                field=name,
                message=msg,
                current_value=value,
            )

    return None


def _validate_cross_field(
    config: Dict[str, Any],
    fields: Dict[str, ConfigField],
    trace_records: Optional[Dict[str, TraceRecord]] = None,
) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []

    save = config.get("save", True)
    save_period = config.get("save_period", -1)
    if isinstance(save, bool) and isinstance(save_period, int):
        if save is False and save_period > 0:
            errors.append(ValidationError(
                field="save_period",
                message="save 为 false 时 save_period 不应大于 0（已禁用保存，却要求周期保存，自相矛盾）",
                current_value=save_period,
            ))

    val = config.get("val", True)
    patience = config.get("patience", 50)
    if isinstance(val, bool) and isinstance(patience, int):
        if val is False and patience > 0:
            warnings.append(ValidationWarning(
                field="patience",
                message="val 为 false 时 patience 不会生效（验证已禁用，早停不会触发）",
                current_value=patience,
            ))

    return errors, warnings