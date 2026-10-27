@echo off
REM ==============================================================
REM Floorplan to Blender 3D Generator - Windows Launcher
REM Recommended Python version: Python 3.10, 3.11, or 3.12
REM ==============================================================

echo [1/3] Checking Python installation...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.11 or 3.12 from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [2/3] Creating Python virtual environment (venv)...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/3] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ==============================================================
echo Starting Floorplan to Blender 3D Web App...
echo Open your browser to: http://localhost:5000
echo Press Ctrl+C in this terminal to stop the server.
echo ==============================================================
echo.

python app.py
pause
