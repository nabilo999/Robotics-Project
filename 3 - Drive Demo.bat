@echo off
REM Drives forward, turns left 90 degrees, drives forward, stops.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_simulation.ps1" demo
echo.
pause
