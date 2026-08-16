@echo off
title Offline Translator
cd /d "%~dp0"
echo.
echo  ============================================
echo   Starting Offline Translator...
echo   Your browser will open automatically.
echo   Keep this window open while using the app.
echo  ============================================
echo.
python\python.exe app.py
if %errorlevel% neq 0 (
    echo.
    echo  Something went wrong.
    pause
)
