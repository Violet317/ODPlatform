# ADR-002: 路径中心化策略

## 状态
已接受

## 背景
在大型 Python 项目中，模块之间互相 import 时经常需要定位项目根目录。
过去常见做法有：
- `os.path.dirname(__file__)` + 多层 `../..`（脆弱，重构就断）
- 硬编码绝对路径（不可移植）
- 设置 `PYTHONPATH` 环境变量（依赖外部配置）

我们需要一个 **可靠的、不依赖外部配置的** 路径定位方案。

## 决策
使用 **Marker 文件机制**：在项目根目录放置 `.odp-workspace` 空文件，
`paths.py` 沿着父目录向上搜索，找到标记文件即确定为根目录。

### 核心实现
```python
from functools import cache
from pathlib import Path

WORKSPACE_MARKER = ".odp-workspace"

@cache
def _find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for parent in [current, *current.parents]:
        if (parent / WORKSPACE_MARKER).exists():
            return parent
    raise FileNotFoundError(f"未找到 {WORKSPACE_MARKER}")
```

### 路径常量
所有路径在模块加载时一次性计算，之后通过常量引用：

```python
ROOT_DIR: Path = _find_workspace_root(Path(__file__))
DATA_DIR: Path = ROOT_DIR / "data"
MODELS_DIR: Path = DATA_DIR / "models"
LOGGING_DIR: Path = APP_DIR / "logging"
```

## 备选方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| Marker 文件（选中） | 健壮、可读、IDE友好 | 需多一个空文件 |
| PYTHONPATH | 无需代码处理 | 依赖外部配置，容易忘 |
| importlib.resources | 标准库 | 只能定位包内文件 |
| 环境变量 | 灵活 | 难以跨团队统一 |

## 影响
- 任何模块都可以 `from odp_platform.common.paths import ROOT_DIR` 获取根路径
- 项目移动位置后无需修改任何代码
- 路径计算带 `@cache` 缓存，性能开销仅一次