@echo off
chcp 65001 >nul
echo ============================================
echo   ODPlatform 一键启动
echo ============================================
echo.
echo 启动 FastAPI 后端...
start "ODPlatform-Backend" /B python apps\web-backend\main.py

timeout /t 3 /nobreak >nul

echo 启动 Streamlit 前端...
start "ODPlatform-Frontend" /B python -m streamlit run apps\web-frontend\app.py --server.port 8501

timeout /t 2 /nobreak >nul
echo.
echo 启动完成！浏览器自动打开...
start http://localhost:8501
echo.
echo 关闭本窗口即可停止所有服务。
pause