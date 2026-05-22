#!/usr/bin/env python
# @FileName  :performance_utils.py
# @Time      :2026/5/19
# @Author    :MuU
# @Project   :ODPlatform
# @Function  :性能记录工具 —— 计时、指标追踪、训练历史记录

import csv
import json
import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# time_it 装饰器 —— 通用执行时间测试
# ============================================================

def time_it(
    iterations: int = 1,
    name: str = None,
    logger_instance: logging.Logger = None,
):
    """
    通用执行时间测试装饰器。

    用法:
        @time_it(name="训练一个epoch", iterations=5)
        def train_epoch():
            ...

        @time_it()  # 默认执行1次
        def fast_func():
            ...

    Args:
        iterations: 执行次数，默认为1
        name: 执行操作的名称，默认为函数名
        logger_instance: 日志实例对象，默认为 performance_utils 的 logger
    """
    log = logger_instance if logger_instance is not None else logger

    def _format_time_auto_unit(seconds: float | int) -> str:
        """自动选择合适的时间单位。"""
        if seconds < 0.001:
            return f"{seconds * 1_000_000:.3f} 微秒"
        elif seconds < 1.0:
            return f"{seconds * 1_000:.3f} 毫秒"
        elif seconds < 60.0:
            return f"{seconds:.3f} 秒"
        elif seconds < 3600.0:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins:.0f} 分钟 {secs:.3f} 秒"
        else:
            hours = int(seconds // 3600)
            remain = seconds % 3600
            mins = int(remain // 60)
            secs = remain % 60
            return f"{hours:.0f} 小时 {mins:.0f} 分钟 {secs:.3f} 秒"

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            total = 0.0
            result = None
            for _ in range(iterations):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                end = time.perf_counter()
                total += end - start

            display_name = name if name is not None else func.__name__
            avg = total / iterations
            avg_str = _format_time_auto_unit(avg)

            if iterations == 1:
                log.info(f"性能报告: {display_name} 执行耗时 {avg_str}")
            else:
                total_str = _format_time_auto_unit(total)
                log.info(
                    f"性能报告: {display_name} 执行了 {iterations} 次, "
                    f"总耗时 {total_str}, 平均耗时 {avg_str}"
                )

            return result
        return wrapper
    return decorator


# ============================================================
# 基础计时器
# ============================================================

@contextmanager
def timer(name: str = "Operation", log_level: int = logging.INFO) -> Generator[None, None, float]:
    """
    上下文管理器计时器，自动记录耗时。

    Args:
        name: 操作名称
        log_level: 日志级别

    Yields:
        耗时（秒）
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.log(log_level, f"{name} 完成, 耗时 {elapsed:.4f} 秒")


def timed(func: Callable) -> Callable:
    """
    装饰器：自动测量函数执行时间。

    用法:
        @timed
        def train_epoch():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start
            logger.info(f"{name} 执行完毕, 耗时 {elapsed:.4f} 秒")
    return wrapper


# ============================================================
# 指标记录器
# ============================================================

@dataclass
class MetricSnapshot:
    """单次指标快照。"""
    step: int
    value: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MetricTracker:
    """
    指标追踪器 —— 记录某个指标在训练过程中的变化。

    用法:
        loss_tracker = MetricTracker("train_loss")
        loss_tracker.record(1, 2.345)
        loss_tracker.record(2, 1.234)
        print(loss_tracker.summary())
    """

    def __init__(self, name: str):
        self.name = name
        self.history: list[MetricSnapshot] = []

    def record(self, step: int, value: float) -> None:
        """记录一个指标值。"""
        self.history.append(MetricSnapshot(step=step, value=value))

    @property
    def latest(self) -> float | None:
        """获取最新值。"""
        return self.history[-1].value if self.history else None

    @property
    def best(self) -> float | None:
        """获取最佳值（最小值）。"""
        return min(s.value for s in self.history) if self.history else None

    @property
    def average(self) -> float | None:
        """获取平均值。"""
        return sum(s.value for s in self.history) / len(self.history) if self.history else None

    def summary(self) -> dict[str, Any]:
        """返回指标摘要。"""
        if not self.history:
            return {"name": self.name, "count": 0}
        return {
            "name": self.name,
            "count": len(self.history),
            "latest": self.latest,
            "best": self.best,
            "average": self.average,
            "first": self.history[0].value,
        }

    def to_csv(self, path: Path) -> None:
        """将历史记录导出为 CSV 文件。"""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["step", "value", "timestamp"])
            writer.writeheader()
            for s in self.history:
                writer.writerow(asdict(s))
        logger.info(f"指标 '{self.name}' 已导出至 {path}")

    def reset(self) -> None:
        """清空历史。"""
        self.history.clear()


# ============================================================
# 训练运行记录器
# ============================================================

@dataclass
class TrainingRunRecord:
    """
    单次训练运行的完整记录。
    包含所有关键配置和性能指标，可导出为 JSON 用于后续比较分析。
    """
    run_name: str
    model_name: str
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def finish(self, metrics: dict[str, Any]) -> None:
        """结束记录并写入最终指标。"""
        self.end_time = datetime.now().isoformat()
        self.metrics = metrics

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典。"""
        return asdict(self)

    def to_json(self, path: Path) -> None:
        """导出为 JSON 文件。"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"训练记录已保存至 {path}")


class TrainingHistory:
    """
    训练历史管理器 —— 持久化记录所有训练运行。

    用法:
        history = TrainingHistory(Path("data/runs"))
        record = history.new_run("exp001", "yolo11n", {...})
        # ... 训练过程 ...
        record.finish({"map50": 0.85, "map50_95": 0.62})
        history.save(record)
        history.list_runs()
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._runs: list[TrainingRunRecord] = []
        self._load_existing()

    def _load_existing(self) -> None:
        """从目录加载已有记录。"""
        if not self.base_dir.exists():
            return
        for f in sorted(self.base_dir.glob("run_*.json")):
            try:
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                    self._runs.append(TrainingRunRecord(**data))
            except Exception as e:
                logger.warning(f"加载历史记录失败 {f}: {e}")

    def new_run(
        self,
        run_name: str,
        model_name: str,
        config: dict[str, Any] | None = None,
    ) -> TrainingRunRecord:
        """创建新的训练运行记录。"""
        record = TrainingRunRecord(
            run_name=run_name,
            model_name=model_name,
            config=config or {},
        )
        self._runs.append(record)
        return record

    def save(self, record: TrainingRunRecord) -> Path:
        """保存单条记录为 JSON 文件。"""
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in record.run_name)
        path = self.base_dir / f"run_{safe_name}.json"
        record.to_json(path)
        return path

    def list_runs(self) -> list[dict[str, Any]]:
        """列出所有训练运行摘要。"""
        return [
            {
                "run_name": r.run_name,
                "model": r.model_name,
                "start": r.start_time,
                "end": r.end_time or "进行中",
                "metrics": r.metrics,
            }
            for r in self._runs
        ]

    def get_run(self, run_name: str) -> TrainingRunRecord | None:
        """按名称查找运行记录。"""
        for r in self._runs:
            if r.run_name == run_name:
                return r
        return None

    def best_run(self, metric_key: str = "map50") -> TrainingRunRecord | None:
        """根据指定指标找到最佳运行。"""
        valid = [r for r in self._runs if metric_key in r.metrics]
        if not valid:
            return None
        return max(valid, key=lambda r: r.metrics[metric_key])

    def to_dataframe_compatible(self) -> list[dict[str, Any]]:
        """返回适合 pandas DataFrame 的扁平化列表。"""
        rows = []
        for r in self._runs:
            row = {
                "run_name": r.run_name,
                "model": r.model_name,
                "start": r.start_time,
                "end": r.end_time or "",
            }
            row.update(r.metrics)
            rows.append(row)
        return rows


# ============================================================
# 格式化工具
# ============================================================

def format_bytes(num_bytes: int) -> str:
    """将字节数格式化为可读字符串。"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """将秒数格式化为可读时长。"""
    if seconds < 60:
        return f"{seconds:.1f} 秒"
    if seconds < 3600:
        return f"{seconds / 60:.1f} 分钟"
    return f"{seconds / 3600:.2f} 小时"
