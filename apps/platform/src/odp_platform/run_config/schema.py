from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ConfigField:
    name: str
    type: type
    default: Any
    description: str
    group: str
    examples: tuple[str, ...] = ()
    advice: tuple[str, ...] = ()
    sensitive: bool = False
    ge: Optional[float] = None
    le: Optional[float] = None
    choices: Optional[tuple[str, ...]] = None
    validator: Optional[Callable[[Any], Optional[str]]] = None


@dataclass(frozen=True)
class TraceRecord:
    field: str
    final_value: Any
    sources: tuple[tuple[str, Any], ...]

    def human_readable(self) -> str:
        parts = [f"  [{self.field}] 最终值 = {self.final_value!r}"]
        for i, (source, val) in enumerate(self.sources):
            arrow = "←" if i < len(self.sources) - 1 else "✓"
            parts.append(f"    {arrow} {source}: {val!r}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "final_value": self.final_value,
            "sources": [{"source": s, "value": v} for s, v in self.sources],
        }


@dataclass(frozen=True)
class TraceReport:
    records: tuple[TraceRecord, ...]

    def human_readable(self) -> str:
        return "\n\n".join(r.human_readable() for r in self.records)

    def to_dict(self) -> dict:
        return {"records": [r.to_dict() for r in self.records]}


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str
    current_value: Any
    trace: Optional[TraceRecord] = None

    def to_dict(self) -> dict:
        d: dict = {
            "field": self.field,
            "message": self.message,
            "current_value": self.current_value,
        }
        if self.trace:
            d["trace"] = self.trace.to_dict()
        return d


@dataclass(frozen=True)
class ValidationWarning:
    field: str
    message: str
    current_value: Any

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "message": self.message,
            "current_value": self.current_value,
        }


@dataclass
class ConfigBundle:
    task: str
    config: dict
    trace: TraceReport
    errors: list[ValidationError]
    warnings: list[ValidationWarning]

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def to_ultralytics_args(self) -> dict:
        internal_fields = {"task", "experiment_name"}
        return {k: v for k, v in self.config.items() if v is not None and k not in internal_fields}

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "config": self.config,
            "trace": self.trace.to_dict(),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "valid": self.valid,
        }

    def to_report_dict(self, mask_sensitive: bool = True) -> dict:
        """生成适合人类阅读的报告字典（可选择脱敏敏感字段）。"""
        config = self.config.copy()
        trace_dict = self.trace.to_dict()

        if mask_sensitive:
            from odp_platform.run_config.registry import get_field
            for key in list(config.keys()):
                try:
                    f = get_field(key)
                    if f.sensitive:
                        config[key] = "***"
                except KeyError:
                    pass
            for record in trace_dict.get("records", []):
                try:
                    f = get_field(record["field"])
                    if f.sensitive:
                        record["final_value"] = "***"
                        for src in record.get("sources", []):
                            src["value"] = "***"
                except KeyError:
                    pass

        return {
            "task": self.task,
            "config": config,
            "trace": trace_dict,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "valid": self.valid,
        }


SNAPSHOT_VERSION = 1


@dataclass(frozen=True)
class ConfigSnapshot:
    """配置快照：支持序列化/反序列化的实验配置冻结副本。

    用于实验复现（FR-23）：将一份配置导出为完整的可序列化快照，
    日后可据此精确恢复配置。
    """
    version: int = SNAPSHOT_VERSION
    task: str = ""
    config: dict = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "task": self.task,
            "config": self.config,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ConfigSnapshot:
        return cls(
            version=data.get("version", SNAPSHOT_VERSION),
            task=data.get("task", ""),
            config=data.get("config", {}),
            created_at=data.get("created_at", ""),
        )

    @classmethod
    def from_bundle(cls, bundle: ConfigBundle) -> ConfigSnapshot:
        from datetime import datetime, timezone
        return cls(
            task=bundle.task,
            config=dict(bundle.config),
            created_at=datetime.now(timezone.utc).isoformat(),
        )