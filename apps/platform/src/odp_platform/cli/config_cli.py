from __future__ import annotations

import argparse
import sys
from pathlib import Path

from odp_platform.common.constants import RunTask
from odp_platform.common.paths import CONFIGS_DIR
from odp_platform.run_config import build_config, generate_template_to_file, list_fields, restore_from_snapshot, save_snapshot_to_file, load_snapshot_from_file, ConfigSnapshot

import logging
logger = logging.getLogger("odp-config")


def main():
    try:
        _main()
    except KeyboardInterrupt:
        logger.warning("用户中断")
        sys.exit(3)
    except Exception as e:
        logger.exception("未预期的错误: %s", e)
        sys.exit(3)


def _main():
    parser = argparse.ArgumentParser(
        prog="odp-config",
        description="ODPlatform 运行配置工具",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="生成配置模板 YAML")
    gen.add_argument("--task", "-t", required=True, choices=RunTask.all(),
                     help="任务类型")
    gen.add_argument("--output", "-o", default=None,
                     help="输出路径（默认: configs/<task>_config.yaml）")
    gen.add_argument("--force", "-f", action="store_true",
                     help="覆盖已存在的文件")
    gen.add_argument("--no-backup", action="store_true",
                     help="覆盖时不备份原文件")

    val = sub.add_parser("validate", help="验证配置 YAML")
    val.add_argument("--config", "-c", required=True,
                     help="配置 YAML 文件路径")
    val.add_argument("--task", "-t", required=True, choices=RunTask.all(),
                     help="任务类型")
    val.add_argument("--preview", action="store_true",
                     help="仅预览合并结果，不执行验证")

    trace_p = sub.add_parser("trace", help="查看配置字段来源追溯")
    trace_p.add_argument("--config", "-c", required=True,
                         help="配置 YAML 文件路径")
    trace_p.add_argument("--task", "-t", required=True, choices=RunTask.all(),
                         help="任务类型")
    trace_p.add_argument("--field", "-f", default=None,
                         help="指定字段名（不指定则显示全部）")

    snap = sub.add_parser("snapshot", help="导出/恢复配置快照")
    snap_sub = snap.add_subparsers(dest="snapshot_cmd", required=True)

    snap_export = snap_sub.add_parser("export", help="导出配置快照")
    snap_export.add_argument("--output", "-o", default="config_snapshot.json",
                             help="输出路径（默认: config_snapshot.json）")
    snap_export.add_argument("--yaml", "-y", required=True,
                             help="配置 YAML 文件路径")
    snap_export.add_argument("--task", "-t", required=True, choices=RunTask.all(),
                             help="任务类型")
    snap_export.add_argument("--mask-sensitive", action="store_true",
                             help="脱敏后导出")

    snap_restore = snap_sub.add_parser("restore", help="从快照恢复配置（含验证）")
    snap_restore.add_argument("--input", "-i", required=True,
                              help="快照 JSON 文件路径")
    snap_restore.add_argument("--output", "-o", default=None,
                              help="恢复后的 YAML 路径（不指定则打印到终端）")

    args = parser.parse_args()

    if args.command == "generate":
        output = args.output or str(CONFIGS_DIR / f"{args.task}_config.yaml")
        result = generate_template_to_file(
            task=args.task,
            output_path=Path(output),
            force=args.force,
            backup=not args.no_backup,
        )
        print(result)

    elif args.command == "validate":
        bundle = build_config(
            task=args.task,
            yaml_path=Path(args.config),
            preview_only=args.preview,
        )
        if bundle.errors:
            print(f"验证失败: {len(bundle.errors)} 个错误")
            for err in bundle.errors:
                print(f"  [ERROR] {err.field}: {err.message} (当前值: {err.current_value!r})")
            if bundle.errors[0].trace:
                print("\n来源追溯:")
                print(bundle.errors[0].trace.human_readable())
        else:
            print(f"验证通过 ({len(bundle.warnings)} 个警告)")
            for w in bundle.warnings:
                print(f"  [WARN] {w.field}: {w.message}")

        sys.exit(0 if bundle.valid else 2)

    elif args.command == "trace":
        bundle = build_config(
            task=args.task,
            yaml_path=Path(args.config),
            preview_only=True,
        )
        print(f"\n配置来源追溯 — 任务: {args.task}\n")
        if args.field:
            filtered = [r for r in bundle.trace.records if r.field == args.field]
            if not filtered:
                print(f"未找到字段 '{args.field}'")
                return
            print(filtered[0].human_readable())
        else:
            print(bundle.trace.human_readable())

    elif args.command == "snapshot":
        if args.snapshot_cmd == "export":
            bundle = build_config(
                task=args.task,
                yaml_path=Path(args.yaml),
                preview_only=True,
            )
            if bundle.errors:
                print(f"配置有误，无法导出快照: {bundle.errors[0].message}")
                sys.exit(2)
            snapshot = ConfigSnapshot.from_bundle(bundle)
            path = save_snapshot_to_file(snapshot, Path(args.output))
            print(f"快照已导出: {path}")

        elif args.snapshot_cmd == "restore":
            snapshot = load_snapshot_from_file(Path(args.input))
            bundle = restore_from_snapshot(snapshot)
            if bundle.valid:
                print("快照恢复验证通过")
            else:
                print(f"快照恢复验证失败: {len(bundle.errors)} 个错误")
                for err in bundle.errors:
                    print(f"  [ERROR] {err.field}: {err.message}")

            if args.output:
                import yaml
                output_config = bundle.config.copy()
                output_config["task"] = bundle.task
                Path(args.output).write_text(
                    yaml.dump(output_config, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                print(f"配置已写入: {args.output}")
            else:
                import json
                print(json.dumps(
                    bundle.to_report_dict(mask_sensitive=True),
                    ensure_ascii=False, indent=2,
                ))


if __name__ == "__main__":
    main()