"""odp-backend CLI — 启动 FastAPI 后端服务"""

from __future__ import annotations

import subprocess
import sys

from odp_platform.common.paths import ROOT_DIR

BACKEND_DIR = ROOT_DIR / "apps" / "web-backend"


def main() -> None:
    """启动 ODPlatform API 服务（FastAPI + SQLite）。"""
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(BACKEND_DIR),
        check=False,
    )