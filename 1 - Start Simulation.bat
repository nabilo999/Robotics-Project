@echo off
REM Starts Docker (if needed), the ROS container, Gazebo + TurtleBot3, and opens the browser desktop.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_simulation.ps1" start %*
echo.
pause
