from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from odp_platform.run_config.registry import list_fields
from odp_platform.run_config.schema import ConfigField

TEMPLATE_HEADER = """# ============================================================
#  ODPlatform 运行配置模板
#  生成时间: {timestamp}
#  任务类型: {task}
#  说明: 编辑此文件后通过 `odp-config validate` 验证
# ============================================================

"""

TEMPLATE_FOOTER = """
# ============================================================
#  常见问题
# ============================================================
# Q: 编辑后如何验证？
# A: odp-config validate --config 此文件路径
#
# Q: 如何生成其他任务的模板？
# A: odp-config generate --task val   (验证)
#    odp-config generate --task predict (推理)
#
# Q: 如何恢复默认值？
# A: 删除对应字段行，系统会用代码默认值
# ============================================================
"""


def generate_template(task: str) -> str:
    fields = list_fields(task)
    groups = _group_fields(fields)

    lines: List[str] = [
        TEMPLATE_HEADER.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            task=task,
        )
    ]

    for group_name, group_fields in groups:
        lines.append(f"# {'=' * 60}")
        lines.append(f"#  {group_name}")
        lines.append(f"# {'=' * 60}")

        for field in group_fields:
            lines.extend(_render_field(field))

        lines.append("")

    lines.append(TEMPLATE_FOOTER)
    return "\n".join(lines)


def generate_template_to_file(task: str, output_path: Path, force: bool = False, backup: bool = True) -> str:
    if output_path.exists() and not force:
        return f"跳过: {output_path} 已存在（使用 --force 覆盖）"

    if output_path.exists() and force and backup:
        bak = output_path.with_suffix(f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}.yaml")
        output_path.rename(bak)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = generate_template(task)
    output_path.write_text(content, encoding="utf-8")
    return f"已写入: {output_path}"


def _group_fields(fields: Dict[str, ConfigField]) -> List[tuple[str, List[ConfigField]]]:
    groups: Dict[str, List[ConfigField]] = {}
    for name, field in fields.items():
        g = field.group
        if g not in groups:
            groups[g] = []
        groups[g].append(field)

    result: List[tuple[str, List[ConfigField]]] = []
    for g in sorted(groups):
        result.append((g, groups[g]))
    return result


def _render_field(field: ConfigField) -> List[str]:
    lines: List[str] = []

    if field.description:
        lines.append(f"# {field.description}")

    if field.examples:
        ex = ", ".join(field.examples)
        lines.append(f"# 示例: {ex}")

    if field.advice:
        for a in field.advice:
            lines.append(f"# 建议: {a}")

    if field.ge is not None or field.le is not None:
        bounds = []
        if field.ge is not None:
            bounds.append(f"最小值: {field.ge}")
        if field.le is not None:
            bounds.append(f"最大值: {field.le}")
        lines.append(f"# 范围: {', '.join(bounds)}")

    if field.choices:
        lines.append(f"# 可选值: {', '.join(field.choices)}")

    if field.sensitive:
        lines.append("# ⚠ 敏感字段")

    default_repr = _render_default(field.default)
    lines.append(f"{field.name}: {default_repr}")
    return lines


def _render_default(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str) and value == "":
        return "''"
    if isinstance(value, str):
        if ":" in value or "#" in value:
            return f"'{value}'"
        return value
    return str(value)