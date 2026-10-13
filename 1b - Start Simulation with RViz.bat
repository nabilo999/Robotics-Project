@echo off
REM Same as Start Simulation, but also opens RViz (shows LiDAR points). Slower on this laptop.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_simulation.ps1" start -RViz
echo.
pause
