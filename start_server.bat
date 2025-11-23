@echo off
title Interactive Test UI Server
color 0A

echo.
echo ========================================
echo   Interactive Test UI Application
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if required packages are installed
echo Checking dependencies...
py -c "import fastapi, uvicorn, pdfplumber, jinja2" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Required packages are missing!
    echo.
    echo Installing dependencies...
    py -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo Please run manually: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo [OK] Dependencies installed
echo.

REM Check if templates directory exists
if not exist "templates" (
    echo [ERROR] Templates directory not found!
    echo Please make sure you're running this from the project root directory.
    pause
    exit /b 1
)

echo [OK] Templates directory found
echo.

REM Check if port 8000 is available
netstat -ano | findstr :8000 >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port 8000 is already in use!
    echo Another application may be using this port.
    echo.
    echo Do you want to continue anyway? (Y/N)
    set /p continue=
    if /i not "%continue%"=="Y" (
        echo Server startup cancelled.
        pause
        exit /b 1
    )
)

echo ========================================
echo Starting server...
echo ========================================
echo.
echo Server URL: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the server
py test_ui_app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Server failed to start!
    echo Check the error messages above for details.
    echo.
    pause
    exit /b 1
)

pause

