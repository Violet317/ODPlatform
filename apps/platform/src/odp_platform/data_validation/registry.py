from __future__ import annotations

import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from odp_platform.common.constants import DETAILS_PREVIEW_LIMIT

if sys.version_info >= (3, 10):
    from types import NoneType
else:
    NoneType = type(None)


@dataclass(frozen=True)
class CheckEntry:
    name: str
    func: Callable[..., Any]
    enabled: bool = True


class CheckSeverity:
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    PASS = "PASS"

    _RANK = {ERROR: 3, WARNING: 2, INFO: 1, PASS: 0}

    @classmethod
    def rank(cls, level: str) -> int:
        return cls._RANK.get(level, 0)


@dataclass
class CheckResult:
    name: str
    severity: str
    summary: str
    details: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.severity in (CheckSeverity.PASS, CheckSeverity.INFO)


@dataclass
class CheckContext:
    yaml_path: Path
    snapshot: Optional["DatasetSnapshot"] = None

    def __post_init__(self):
        from pathlib import Path as P
        if not isinstance(self.yaml_path, P):
            object.__setattr__(self, "yaml_path", P(self.yaml_path))


_REGISTRY: Dict[str, CheckEntry] = {}
_INITIALIZED: bool = False


def check(name: str):
    if name in _REGISTRY:
        raise ValueError(f"重复注册的 check 名: {name}")
    def decorator(func):
        _REGISTRY[name] = CheckEntry(name=name, func=func)
        return func
    return decorator


def get_check(name: str) -> CheckEntry:
    _lazy_init()
    if name not in _REGISTRY:
        raise ValueError(f"未注册的 check: {name}")
    return _REGISTRY[name]


def list_checks() -> List[str]:
    _lazy_init()
    return list(_REGISTRY.keys())


def _lazy_init():
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True
    import odp_platform.data_validation.checks as checks_pkg
    for importer, modname, ispkg in pkgutil.iter_modules(checks_pkg.__path__):
        if modname.startswith("_"):
            continue
        __import__(f"odp_platform.data_validation.checks.{modname}")


def _clear_registry():
    _REGISTRY.clear()
    global _INITIALIZED
    _INITIALIZED = False