from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from odp_platform.common.paths import CONFIGS_DIR


def load_yaml(path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    error: Optional[str] = None
    data: Dict[str, Any] = {}

    try:
        raw = yaml.safe_load(path.read_text("utf-8"))
    except FileNotFoundError:
        error = f"文件不存在: {path}"
        return data, error
    except yaml.YAMLError as e:
        error = f"YAML 解析失败: {e}"
        return data, error
    except UnicodeDecodeError:
        try:
            raw = yaml.safe_load(path.read_text("gbk"))
        except Exception as e:
            error = f"编码尝试均失败: {e}"
            return data, error

    if raw is None:
        return data, None
    if not isinstance(raw, dict):
        error = f"YAML 顶层结构应为字典，实际为 {type(raw).__name__}"
        return data, error

    data = {k: v for k, v in raw.items() if v is not None}
    return data, error


def resolve_yaml_path(name_or_path: str) -> Path:
    p = Path(name_or_path)
    if p.is_absolute():
        return p
    if p.suffix in (".yaml", ".yml"):
        return p.resolve()
    return (CONFIGS_DIR / "datasets" / f"{name_or_path}.yaml").resolve()


def parse_cli_args(args: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in args.items() if v is not None and not k.startswith("_")}