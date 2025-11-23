@echo off
echo ========================================
echo USABO Test UI - GitHub Deployment
echo ========================================
echo.

REM Check if remote already exists
git remote get-url origin >nul 2>&1
if %errorlevel% == 0 (
    echo Remote 'origin' already exists.
    echo Current remote URL:
    git remote get-url origin
    echo.
    set /p UPDATE="Do you want to update it? (y/n): "
    if /i "%UPDATE%"=="y" (
        git remote remove origin
    ) else (
        echo Keeping existing remote. Exiting.
        exit /b
    )
)

echo.
echo Creating GitHub repository 'usabo'...
echo.
echo Please choose one of the following options:
echo.
echo Option 1: Create repo via GitHub website (Recommended)
echo   1. Go to https://github.com/new
echo   2. Repository name: usabo
echo   3. Choose Public or Private
echo   4. DO NOT initialize with README (we already have one)
echo   5. Click "Create repository"
echo   6. Copy the repository URL shown
echo   7. Press any key when ready to continue...
pause >nul

echo.
set /p REPO_URL="Enter your GitHub repository URL (e.g., https://github.com/YOUR_USERNAME/usabo.git): "

if "%REPO_URL%"=="" (
    echo Error: Repository URL is required.
    exit /b 1
)

echo.
echo Adding remote repository...
git remote add origin %REPO_URL%

echo.
echo Pushing code to GitHub...
git branch -M main
git push -u origin main

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo SUCCESS! Repository deployed to GitHub
    echo ========================================
    echo.
    echo Your repository is available at:
    echo %REPO_URL%
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Failed to push to GitHub
    echo ========================================
    echo.
    echo Possible issues:
    echo - Authentication required (use GitHub token)
    echo - Repository doesn't exist yet
    echo - Network connectivity issues
    echo.
    echo To push manually, run:
    echo   git push -u origin main
    echo.
)

pause

