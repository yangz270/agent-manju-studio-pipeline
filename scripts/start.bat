@echo off
chcp 65001 > nul
echo ======================================================================
echo    AI Donghua Studio - Multi-Agent Pipeline Launcher
echo ======================================================================
echo.
echo [0/2] Checking required API keys ...
python scripts/preflight_check.py
if errorlevel 1 (
    echo.
    echo Launch aborted: required API keys are missing.
    echo Run:  cp .env.example .env   then fill in your keys.
    echo.
    pause
    exit /b 1
)
echo.
echo [1/2] Environment health check ...
python scripts/health_check.py
echo.
echo [2/2] Running pipeline smoke test ...
python examples/run_pipeline_demo.py
echo.
pause
