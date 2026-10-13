@echo off
REM Checks that the LiDAR (/scan) publishes and the robot moves on /cmd_vel. Simulation must be running.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_simulation.ps1" check
echo.
pause
