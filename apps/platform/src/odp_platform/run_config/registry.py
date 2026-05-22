from __future__ import annotations

from typing import Dict, List, Optional

from odp_platform.run_config.schema import ConfigField

_FIELD_REGISTRY: Dict[str, ConfigField] = {}
_LOADED = False


def register_field(field: ConfigField) -> ConfigField:
    if field.name in _FIELD_REGISTRY:
        return _FIELD_REGISTRY[field.name]
    _FIELD_REGISTRY[field.name] = field
    return field


def get_field(name: str) -> ConfigField:
    _lazy_init()
    if name not in _FIELD_REGISTRY:
        raise KeyError(f"未知字段 '{name}'，可用字段: {list(_FIELD_REGISTRY)}")
    return _FIELD_REGISTRY[name]


def list_fields(task: Optional[str] = None) -> Dict[str, ConfigField]:
    _lazy_init()
    if task is None:
        return dict(_FIELD_REGISTRY)
    return {
        name: f
        for name, f in _FIELD_REGISTRY.items()
        if f.group.startswith(task)
    }


def field_names(task: Optional[str] = None) -> List[str]:
    return list(list_fields(task).keys())


def _lazy_init():
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    import pkgutil
    import importlib
    import odp_platform.run_config.fields
    for importer, modname, ispkg in pkgutil.iter_modules(
        odp_platform.run_config.fields.__path__,
    ):
        if modname.startswith("_"):
            continue
        importlib.import_module(f"odp_platform.run_config.fields.{modname}")