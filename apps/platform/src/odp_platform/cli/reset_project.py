#!/usr/bin/env python
# @FileName  :reset_project.py
# @Time      :2026/5/20
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :odp-reset 项目重置工具 —— 安全、可追溯地清理运行时产物

from __future__ import annotations

import argparse
import getpass
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from odp_platform import __version__
from odp_platform.common.logging_utils import get_logger
from odp_platform.common.paths import (
    META_LOGGING_DIR,
    PRETRAINED_MODELS_DIR,
    RAW_DATA_DIR,
    ROOT_DIR,
    get_dirs_to_reset,
    is_protected,
)
from odp_platform.common.string_utils import format_table_row, format_table_separator

logger = get_logger(
    base_path=META_LOGGING_DIR,
    log_type="reset_project",
    temp_log=False,
)

CONFIRM_KEYWORD = "RESET"
LINE_WIDTH = 70


# ============================================================
#  工具函数
# ============================================================

def _format_size(bytes_size: int) -> str:
    """二进制单位换算 —— 统一 1024 进制以避免单位混淆。"""
    if bytes_size >= 1024 ** 3:
        return f"{bytes_size / (1024 ** 3):.2f} GiB"
    if bytes_size >= 1024 ** 2:
        return f"{bytes_size / (1024 ** 2):.2f} MiB"
    if bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KiB"
    return f"{bytes_size} B"


def _on_rm_error(func, path, exc_info):
    """
    shutil.rmtree 错误回调 —— 处理 Windows 只读文件。

    Windows 上某些被 git checkout 出来的文件会被标记只读，
    shutil.rmtree 会触发 PermissionError。改成可写后重试。
    Linux/macOS 上 chmod + retry 也是无害的，可以跨平台使用。
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        raise  # 交回上层抛


def _audit_context() -> dict:
    """收集审计上下文字段。"""
    try:
        git_rev = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_rev = "(not a git repo)"

    return {
        "user": getpass.getuser(),
        "pid": os.getpid(),
        "git_rev": git_rev,
        "argv": sys.argv,
        "cwd": os.getcwd(),
    }


def _scan_targets() -> tuple[list[tuple[Path, int, int]], list[Path]]:
    """
    扫描所有目标目录。

    Returns:
        (deletable, skipped)
        deletable: 可删除的目录列表 (path, 文件数, 总字节)
        skipped:   跳过的目录列表（受保护或不存在）
    """
    deletable: list[tuple[Path, int, int]] = []
    skipped: list[Path] = []

    for d in get_dirs_to_reset():
        if is_protected(d):
            logger.warning(f"⛔ 拒绝处理受保护目录（配置可能有误）: {d}")
            skipped.append(d)
            continue

        if not d.exists():
            skipped.append(d)
            continue

        file_count = 0
        total_size = 0
        try:
            for f in d.rglob("*"):
                if f.is_file():
                    file_count += 1
                    try:
                        total_size += f.stat().st_size
                    except OSError:
                        pass
        except OSError as e:
            logger.warning(f"扫描 {d} 时出错: {e}")

        deletable.append((d, file_count, total_size))

    return deletable, skipped


def _print_plan(
    deletable: list[tuple[Path, int, int]],
    skipped: list[Path],
    will_actually_delete: bool,
) -> None:
    """打印清理计划表格。"""
    if will_actually_delete:
        logger.warning("⚠️  即将删除以下目录".center(LINE_WIDTH, "="))
    else:
        logger.info("📋 [DRY-RUN] 计划如下（未实际删除）".center(LINE_WIDTH, "="))

    if not deletable:
        logger.info("（没有可删除的目录 —— 项目已经是干净状态）")
        return

    widths = [40, 12, 14]
    aligns = ["left", "right", "right"]
    logger.info(format_table_row(["目录", "文件数", "大小"], widths, aligns))
    logger.info(format_table_separator(widths))

    total_files = 0
    total_bytes = 0
    for path, count, size in deletable:
        rel = path.relative_to(ROOT_DIR)
        logger.info(format_table_row(
            [str(rel), str(count), _format_size(size)],
            widths, aligns,
        ))
        total_files += count
        total_bytes += size

    logger.info(format_table_separator(widths))
    logger.info(format_table_row(
        ["【合计】", str(total_files), _format_size(total_bytes)],
        widths, aligns,
    ))

    if skipped:
        logger.info("")
        logger.info(f"⏭️  跳过 {len(skipped)} 个目录（受保护或不存在）")

    logger.info("")
    logger.info("✅ 以下重要目录【不会】被动:")
    logger.info(f"  - 原始数据: {RAW_DATA_DIR.relative_to(ROOT_DIR)}/")
    logger.info(f"  - 预训练权重: {PRETRAINED_MODELS_DIR.relative_to(ROOT_DIR)}/")
    logger.info("  - 所有代码、文档、配置（进 git 的内容）")


def _confirm(deletable_count: int) -> bool:
    """
    交互式确认。

    刻意使用 print 而非 logger —— 这是视觉打断设计：
    让用户的眼睛从"扫日志"模式切换到"主动决策"模式，
    避免误按回车造成不可逆操作。这是工业级危险操作的标准设计。
    """
    print()
    print("=" * LINE_WIDTH)
    print(f"⚠️  你正要删除 {deletable_count} 个目录的内容。这个操作不可撤销。")
    print(f"⚠️  如果确认，请精确输入大写的 {CONFIRM_KEYWORD!r}（其他任何输入都会取消）:")
    print("=" * LINE_WIDTH)
    try:
        user_input = input("> ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        return False
    return user_input == CONFIRM_KEYWORD


def _delete_one(
    path: Path,
    idx: int,
    total: int,
    file_count: int,
    size: int,
) -> str | None:
    """删除单个目录，带进度提示。返回 None=成功，字符串=失败原因。"""
    # 防御性二次检查 —— 防止 _scan_targets 和 _execute_delete 之间受保护目录变更
    if is_protected(path):
        logger.error(f"[{idx}/{total}] ⛔ 删除前检查失败，跳过: {path}")
        return "受保护目录"

    rel = path.relative_to(ROOT_DIR)
    size_str = _format_size(size)

    if size > 1024 ** 3:
        logger.warning(
            f"[{idx}/{total}] 正在删除 {rel} ({size_str}, {file_count} 个文件)"
            f" —— 这可能需要一会..."
        )
    else:
        logger.info(f"[{idx}/{total}] 删除 {rel} ({size_str}, {file_count} 个文件)")

    try:
        shutil.rmtree(path, onerror=_on_rm_error)
        logger.info(f"[{idx}/{total}] ✅ 已删除: {rel}")
        return None
    except OSError as e:
        logger.error(f"[{idx}/{total}] ❌ 删除失败 {rel}: {e}")
        return str(e)


def _execute_delete(deletable: list[tuple[Path, int, int]]) -> None:
    """执行批量删除。失败记录日志但不影响退出码（非致命）。"""
    total = len(deletable)
    success: list[Path] = []
    failed: list[tuple[Path, str]] = []

    for idx, (path, file_count, size) in enumerate(deletable, 1):
        reason = _delete_one(path, idx, total, file_count, size)
        if reason is None:
            success.append(path)
        else:
            failed.append((path, reason))

    logger.info("")
    logger.info("=" * LINE_WIDTH)
    if failed:
        logger.warning(f"完成: 成功 {len(success)} 个，失败 {len(failed)} 个")
        for p, reason in failed:
            logger.warning(f"  - {p.relative_to(ROOT_DIR)}: {reason}")
    else:
        logger.info(f"完成: 成功 {len(success)} 个，失败 0 个")
    logger.info("=" * LINE_WIDTH)


# ============================================================
#  主逻辑
# ============================================================

def reset_project(yes: bool = False, force: bool = False, dry_run: bool = False) -> int:
    """
    Args:
        yes:     --yes，同意删除
        force:   --force，跳过交互确认（仅 yes=True 时有效）
        dry_run: --dry-run，仅预览（默认行为）

    --dry-run 与 --yes 冲突时以 --dry-run 优先。
    """
    logger.info("=" * LINE_WIDTH)
    logger.info("项目重置工具".center(LINE_WIDTH))
    logger.info("=" * LINE_WIDTH)
    logger.info(f"项目根目录: {ROOT_DIR}")

    ctx = _audit_context()
    logger.info(
        f"审计上下文: user={ctx['user']} pid={ctx['pid']} "
        f"git={ctx['git_rev'][:8]} argv={' '.join(map(str, ctx['argv']))}"
    )
    logger.info("=" * LINE_WIDTH)

    # 处理标志冲突
    if dry_run and yes:
        logger.warning("⚠️  同时给了 --dry-run 和 --yes，以 --dry-run 为准（安全优先）")
        yes = False

    deletable, skipped = _scan_targets()
    _print_plan(deletable, skipped, will_actually_delete=yes)

    if not deletable:
        return 0

    if not yes:
        logger.info("")
        if dry_run:
            logger.info("💡 这是显式的 --dry-run。要真正执行删除，请加 --yes:")
        else:
            logger.info("💡 默认 dry-run。要真正执行删除，请加 --yes:")
        logger.info("   python scripts/reset_project.py --yes")
        return 0

    if not force:
        if not _confirm(len(deletable)):
            logger.warning("❌ 用户取消，未执行删除")
            return 1

    logger.info("")
    logger.info("开始删除...".center(LINE_WIDTH, "="))
    _execute_delete(deletable)
    return 0


# ============================================================
#  argparse 入口
# ============================================================

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        prog="odp-reset",
        description="ODPlatform 项目重置工具 —— 安全地清理运行时产物",
        epilog=(
            "示例:\n"
            "  odp-reset                    # 默认 dry-run，只预览不删除\n"
            "  odp-reset --yes              # 触发交互确认，输入 RESET 后执行\n"
            "  odp-reset --yes --force      # 跳过交互确认，直接执行\n"
            "  odp-reset --dry-run          # 显式指定 dry-run（默认行为）\n"
            "  odp-reset --dry-run --yes    # --dry-run 优先，忽略 --yes"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="同意删除（触发交互确认，需输入大写 RESET）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="跳过交互确认（仅与 --yes 同时使用有效）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览待删目录，不执行删除（默认行为，此参数用于显式声明）",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ODPlatform v{__version__}",
    )
    return parser.parse_args(argv)


def main() -> int:
    """CLI 主入口。"""
    args = parse_args()
    return reset_project(
        yes=args.yes,
        force=args.force,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
