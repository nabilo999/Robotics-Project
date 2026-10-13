@echo off
REM Drive the robot with the keyboard (w/x = faster/slower, a/d = turn, s = stop).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_simulation.ps1" teleop
echo.
pause
