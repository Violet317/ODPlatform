from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from odp_platform.data_validation.registry import CheckResult, CheckSeverity
from odp_platform.data_validation.snapshot import DatasetSnapshot


@dataclass
class ValidationReport:
    run_id: str
    yaml_path: Path
    snapshot: DatasetSnapshot
    results: List[CheckResult]
    duration_seconds: float
    started_at_iso: str
    run_dir: Optional[Path] = None

    @property
    def overall_severity(self) -> str:
        if not self.results:
            return CheckSeverity.PASS
        return max(
            self.results,
            key=lambda r: CheckSeverity.rank(r.severity),
        ).severity

    @property
    def counts_by_severity(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self.results:
            counts[r.severity] = counts.get(r.severity, 0) + 1
        return counts

    @property
    def exit_code(self) -> int:
        sev = self.overall_severity
        if sev == CheckSeverity.ERROR:
            return 2
        if sev == CheckSeverity.WARNING:
            return 1
        return 0

    @property
    def failed_results(self) -> List[CheckResult]:
        return [r for r in self.results if not r.passed]

    @property
    def report_path(self) -> Optional[Path]:
        if self.run_dir is None:
            return None
        return self.run_dir / "report.json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "yaml_path": str(self.yaml_path),
            "task_type": self.snapshot.task_type,
            "started_at": self.started_at_iso,
            "duration_seconds": round(self.duration_seconds, 3),
            "overall_severity": self.overall_severity,
            "exit_code": self.exit_code,
            "counts": self.counts_by_severity,
            "dataset_summary": {
                "nc": self.snapshot.nc,
                "class_names": list(self.snapshot.class_names),
                "stats_per_split": {
                    split: {
                        "image_count": stat.image_count,
                        "annotated_count": stat.annotated_count,
                        "total_instances": stat.total_instances,
                    }
                    for split, stat in self.snapshot.stats_per_split.items()
                },
            },
            "results": [
                {
                    "name": r.name,
                    "severity": r.severity,
                    "summary": r.summary,
                    "details": r.details,
                }
                for r in self.results
            ],
        }