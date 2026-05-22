#!/usr/bin/env python
# @FileName  :paths.py
# @Time      :2026/5/19 09:58:22
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :路径中心化管理 —— 统一管理项目所有目录路径

from functools import cache
from pathlib import Path

WORKSPACE_MARKER: str = ".odp-workspace"


@cache
def _find_workspace_root(
    start: Path,
    markers: tuple[str, ...] = (WORKSPACE_MARKER,),
) -> Path:
    """
    从 start 开始沿着父目录向上查找，返回包含任一 marker 文件的目录。

    Args:
        start: 起始路径（文件或目录均可）
        markers: 一组 marker 文件名，只要存在一个就视为找到

    Returns:
        找到的 workspace 根目录

    Raises:
        FileNotFoundError: 一直爬到文件系统根目录都没找到 marker 文件
    """
    current = start.resolve()
    if current.is_file():
        current = current.parent

    for parent in [current, *current.parents]:
        for marker in markers:
            if (parent / marker).exists():
                return parent

    raise FileNotFoundError(
        f"未找到 marker 文件 {markers}，请确认仓库根目录下存在 {WORKSPACE_MARKER} 文件"
    )


# ============================================================
#  模块级路径常量（在 import 时一次性计算，后续直接引用）
# ============================================================

# 工作区根目录（由 _find_workspace_root 自动探测）
ROOT_DIR: Path = _find_workspace_root(Path(__file__))

# 【端代码目录】Platform 应用的根
APP_DIR: Path = ROOT_DIR / "apps" / "platform"

# 【共享资产】所有端都可以访问的文件
DATA_DIR: Path = ROOT_DIR / "data"
MODELS_DIR: Path = DATA_DIR / "models"
RUNS_DIR: Path = DATA_DIR / "runs"

# 数据校验运行目录（D4 质检报告持久化）
VALIDATION_RUNS_DIR: Path = RUNS_DIR / "data_validation"

# 运行配置运行目录（D5 配置产物持久化）
CONFIG_RUNS_DIR: Path = RUNS_DIR / "run_config"

# 模型子目录
PRETRAINED_MODELS_DIR: Path = MODELS_DIR / "pretrained"
CHECKPOINTS_DIR: Path = MODELS_DIR / "checkpoints"

# 数据集子目录
RAW_DATA_DIR: Path = DATA_DIR / "raw"

TRAIN_DIR: Path = DATA_DIR / "train"
VAL_DIR: Path = DATA_DIR / "val"
TEST_DIR: Path = DATA_DIR / "test"

TRAIN_IMAGES_DIR: Path = TRAIN_DIR / "images"
TRAIN_LABELS_DIR: Path = TRAIN_DIR / "labels"
VAL_IMAGES_DIR: Path = VAL_DIR / "images"
VAL_LABELS_DIR: Path = VAL_DIR / "labels"
TEST_IMAGES_DIR: Path = TEST_DIR / "images"
TEST_LABELS_DIR: Path = TEST_DIR / "labels"

# 【端私有资产】只属于 platform 这个端的资产文件
CONFIGS_DIR: Path = APP_DIR / "configs"
CONFIGS_DATASETS_DIR: Path = CONFIGS_DIR / "datasets"
LOGGING_DIR: Path = APP_DIR / "logging"
UNIT_TEST_DIR: Path = APP_DIR / "tests"

# 顶层的文档目录【共享给所有人】
DOCS_DIR: Path = ROOT_DIR / "docs"

# 工程基础设施目录
SCRIPTS_DIR: Path = ROOT_DIR / "scripts"

# ============================================================
#  工具元数据目录（先定义，因为 get_dirs_to_initialize 需要引用）
# ============================================================
META_DIR: Path = ROOT_DIR / ".odp-meta"
META_LOGGING_DIR: Path = META_DIR / "logs"


def raw_dataset_root(dataset_name: str) -> Path:
    """返回指定数据集的原始数据根目录: data/raw/<name>/"""
    return RAW_DATA_DIR / dataset_name


def dataset_yaml_path(dataset_name: str) -> Path:
    """返回指定数据集的 data.yaml 配置路径。"""
    return CONFIGS_DATASETS_DIR / f"{dataset_name}.yaml"


def validation_run_dir(run_id: str) -> Path:
    """返回指定 run_id 的数据校验运行目录。"""
    return VALIDATION_RUNS_DIR / run_id


def config_run_dir(run_id: str) -> Path:
    """返回指定 run_id 的运行配置运行目录。"""
    return CONFIG_RUNS_DIR / run_id


def get_dirs_to_initialize() -> list[Path]:
    """
    返回项目启动时需要确保存在的所有目录列表。

    Returns:
        所有需要初始化的目录路径列表
    """
    return [
        DATA_DIR,
        MODELS_DIR,
        RUNS_DIR,
        VALIDATION_RUNS_DIR,
        CONFIG_RUNS_DIR,
        PRETRAINED_MODELS_DIR,
        CHECKPOINTS_DIR,
        RAW_DATA_DIR,
        TRAIN_IMAGES_DIR,
        TEST_IMAGES_DIR,
        VAL_IMAGES_DIR,
        TRAIN_LABELS_DIR,
        TEST_LABELS_DIR,
        VAL_LABELS_DIR,
        CONFIGS_DIR,
        CONFIGS_DATASETS_DIR,
        LOGGING_DIR,
        UNIT_TEST_DIR,
        SCRIPTS_DIR,
        DOCS_DIR,
        META_DIR,
        META_LOGGING_DIR,
    ]


# ============================================================
#  reset_project 工具专用路径/保护机制
# ============================================================

# 受保护目录黑名单（tuple 不可变，防止运行时篡改）
# 任何 reset 操作都不能碰这些目录及其子目录
PROTECTED_DIRS: tuple[Path, ...] = (
    # 项目根与基础设施
    ROOT_DIR,
    ROOT_DIR / ".git",
    ROOT_DIR / ".odp-workspace",
    # 整体应用目录（monorepo 中所有端）
    ROOT_DIR / "apps",
    ROOT_DIR / "packages",
    # 当前端（platform）
    APP_DIR,
    APP_DIR / "src",
    # 工程基础设施
    SCRIPTS_DIR,
    DOCS_DIR,
    CONFIGS_DIR,
    UNIT_TEST_DIR,
    # 工具元数据（审计日志永不被自身清除）
    META_DIR,
    META_LOGGING_DIR,
)


def is_protected(path: Path) -> bool:
    """
    判断给定路径是否受保护（不可被 reset 删除）。

    双向检查：
      1. 路径本身是否受保护目录
      2. 路径是否是某个受保护目录的祖先（防止删祖先间接删受保护后代）
        例如把 ROOT_DIR 加入重置清单时，APP_DIR 是 ROOT_DIR 的后代，
        此时应拦截 ROOT_DIR

    Args:
        path: 要检查的路径

    Returns:
        True 表示受保护，False 表示可安全删除
    """
    resolved = path.resolve(strict=False)
    for protected in PROTECTED_DIRS:
        protected_resolved = protected.resolve(strict=False)
        if resolved == protected_resolved:
            return True
        if protected_resolved.is_relative_to(resolved):
            return True
    return False


def get_dirs_to_reset() -> list[Path]:
    """
    返回 reset_project 工具可清理的目录白名单。

    设计原则：
      - 不是从 get_dirs_to_initialize() 减出来的，而是重新明确列举
      - 只包含运行时产物：训练划分、checkpoints、runs、业务日志
      - 绝对不包含：源代码、配置、原始数据、预训练模型、元数据目录

    Returns:
        可被 reset 清理的目录路径列表
    """
    return [
        RUNS_DIR,
        CHECKPOINTS_DIR,
        TRAIN_DIR,
        VAL_DIR,
        TEST_DIR,
        LOGGING_DIR,
    ]


if __name__ == "__main__":
    print(f"ROOT_DIR (workspace) = {ROOT_DIR}")
    print(f"APP_DIR (platform)   = {APP_DIR}")

    dirs = get_dirs_to_initialize()
    print(f"\n需要初始化的目录共有 {len(dirs)} 个：")
    for d in dirs:
        print(f"  - {d.relative_to(ROOT_DIR)}")
