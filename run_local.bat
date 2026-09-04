@echo off
title PS5 Stock Bot - PlayStation Direct Monitor
echo ===================================================
echo     Starting PlayStation 5 Stock Monitor Bot
echo ===================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo.
echo Launching PS5 Stock Monitor...
python main.py

pause
