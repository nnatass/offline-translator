@echo off
title Downloading AI models for Offline Translator
cd /d "%~dp0"
echo.
echo  ============================================
echo   Downloading AI models (needs internet)
echo   Only needed once. About 2 GB total.
echo  ============================================
echo.
python\python.exe setup_first.py
echo.
pause
