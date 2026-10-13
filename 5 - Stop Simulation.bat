@echo off
REM Stops the simulation and the ROS container to free memory.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_simulation.ps1" down
echo.
pause
