"""一键启动脚本 — 同时启动 FastAPI 后端 + Streamlit 前端。

双击运行或在终端执行：
    python launch.py

完成后自动打开浏览器访问 Streamlit 前端。
按 Ctrl+C 同时关闭两个服务。
"""
from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


def main():
    print("=" * 60)
    print("  ODPlatform 一键启动")
    print("=" * 60)

    # ── 启动 FastAPI 后端 ──
    print("\n[1/3] 启动 FastAPI 后端...")
    backend_dir = ROOT_DIR / "apps" / "web-backend"
    backend_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    # ── 等待后端就绪 ──
    print("[2/3] 等待后端就绪...")
    time.sleep(3)

    # ── 启动 Streamlit 前端 ──
    print("[3/3] 启动 Streamlit 前端...")
    frontend_dir = ROOT_DIR / "apps" / "web-frontend"
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    # ── 打开浏览器 ──
    time.sleep(2)
    print("\n启动完成！自动打开浏览器...")
    webbrowser.open("http://localhost:8501")

    print("\n按 Ctrl+C 停止所有服务...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n正在停止服务...")
        backend_process.terminate()
        frontend_process.terminate()
        print("所有服务已停止")


if __name__ == "__main__":
    main()