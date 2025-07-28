@echo off
echo 🚀 DripEmails SMTP Server Packaging Script for Windows
echo ====================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "core\smtp_server.py" (
    echo ❌ This script must be run from the dripemails.org workspace directory
    echo Please run this script from the directory containing the 'core' folder
    pause
    exit /b 1
)

echo ✅ Python found and directory structure looks correct
echo.

REM Run the packaging script
python package_smtp_server.py

if errorlevel 1 (
    echo.
    echo ❌ Packaging failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ✅ Packaging completed successfully!
echo.
echo 📋 Next Steps:
echo 1. Review the package in the smtp_server directory
echo 2. Push to GitHub: git push -u origin main
echo 3. Upload to PyPI: python -m twine upload dist/*
echo 4. Test installation: pip install dripemails-smtp-server
echo.
pause 