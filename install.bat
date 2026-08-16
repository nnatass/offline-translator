@echo off
title Installing Offline Translator dependencies
cd /d "%~dp0"
echo.
echo  ============================================
echo   Installing Python packages
echo  ============================================
echo.
python\python.exe -m pip install -r requirements.txt --no-warn-script-location
echo.
echo  Done. Next: run setup_first.bat to download AI models.
echo.
pause
