<#
.SYNOPSIS
  One-command launcher for the group-project TurtleBot3 simulation (Docker + ROS 2 Jazzy + Gazebo).

.EXAMPLE
  .\run_simulation.ps1               # start everything (same as: start)
  .\run_simulation.ps1 start -RViz   # also open RViz
  .\run_simulation.ps1 check         # verify LiDAR + movement (sim must be running)
  .\run_simulation.ps1 demo          # drive forward, turn, forward
  .\run_simulation.ps1 teleop        # drive with the keyboard
  .\run_simulation.ps1 shell         # terminal inside the robot computer
  .\run_simulation.ps1 stop          # stop the simulation (container keeps running)
  .\run_simulation.ps1 down          # stop everything and free memory
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "check", "demo", "teleop", "shell", "stop", "down", "status", "build", "help")]
    [string]$Command = "start",
    [switch]$RViz,          # start: also open RViz
    [switch]$NoGui,         # start: no Gazebo window (lighter)
    [switch]$NoBrowser      # start: don't open the browser
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Image = if ($env:COURSE_ROS_IMAGE) { $env:COURSE_ROS_IMAGE } else { "robotics-fall2026:jazzy" }
$DesktopUrl = "http://localhost:6081/vnc.html?autoconnect=1&resize=scale"

# Run a native command without PowerShell 5.1 turning its stderr into errors; return the exit code.
function Invoke-Quiet([scriptblock]$Block) {
    $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { & $Block 2>&1 | Out-Null } finally { $ErrorActionPreference = $old }
    return $LASTEXITCODE
}

function Test-DockerReady { (Invoke-Quiet { docker info }) -eq 0 }

function Start-DockerIfNeeded {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker is not installed. Install Docker Desktop (WSL 2 backend) first."
    }
    if (Test-DockerReady) { return }
    $exe = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (Test-Path $exe) {
        Write-Host "==> Starting Docker Desktop (can take 1-2 minutes) ..."
        Start-Process $exe
    }
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 3
        if (Test-DockerReady) { Write-Host "==> Docker is ready."; return }
    }
    throw "Docker did not start. Open Docker Desktop, close any error/update dialog it shows (do NOT reset to factory defaults), then try again."
}

function Assert-Image {
    if ((Invoke-Quiet { docker image inspect $Image }) -ne 0) {
        throw ("Docker image '$Image' not found. Build it once from the course repo:`n" +
               "  cd ""<path>\robotics-fall2026""; docker compose build   (needs ~12 GB free disk)")
    }
}

function Test-ContainerRunning {
    $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { $id = docker compose ps -q --status running ros 2>$null } finally { $ErrorActionPreference = $old }
    return [bool]$id
}

function Start-Container {
    Start-DockerIfNeeded
    Assert-Image
    $ErrorActionPreference = "Continue"
    $course = docker ps -q --filter "name=robotics-fall2026-course-ros" 2>$null
    $ErrorActionPreference = "Stop"
    if ($course) {
        Write-Warning "The course container (robotics-fall2026) is also running. Stop it to save memory: .\scripts\ros_course.ps1 stop (in the course repo)."
    }
    if (-not (Test-ContainerRunning)) {
        Write-Host "==> Starting the ROS container ..."
        docker compose up -d
        if ($LASTEXITCODE -ne 0) { throw "docker compose up failed." }
    }
}

function Assert-ContainerRunning {
    if (-not (Test-DockerReady) -or -not (Test-ContainerRunning)) {
        throw "The simulation container isn't running. Start it first: .\run_simulation.ps1 start"
    }
}

# Run a bash command inside the container (check $LASTEXITCODE afterwards).
# Uses a terminal when we have one (needed for Ctrl+C and keyboard teleop).
function Invoke-InContainer([string]$BashCommand) {
    $dockerArgs = @("compose", "exec")
    if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) { $dockerArgs += "-T" }
    $dockerArgs += @("ros", "bash", "-lc", $BashCommand)
    $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { & docker @dockerArgs } finally { $ErrorActionPreference = $old }
}

function Open-Desktop {
    if ($NoBrowser) { return }
    for ($i = 0; $i -lt 60; $i++) {
        try {
            Invoke-WebRequest "http://localhost:6081/vnc.html" -UseBasicParsing -TimeoutSec 2 | Out-Null
            Start-Process $DesktopUrl
            return
        } catch { Start-Sleep -Seconds 1 }
    }
    Write-Warning "Browser desktop not reachable yet. Open it manually: $DesktopUrl"
}

$RosEnv = "source /project/scripts/project_env.sh"

Push-Location $ProjectRoot
try {
    switch ($Command) {
        "start" {
            Start-Container
            Open-Desktop
            $launchArgs = "rviz:=$(([string]$RViz.IsPresent).ToLower()) gui:=$(([string](-not $NoGui.IsPresent)).ToLower())"
            Write-Host ""
            Write-Host "Simulation desktop: $DesktopUrl"
            Write-Host "Gazebo appears there in ~30-60 s. Keep this window open; press Ctrl+C here to stop."
            Write-Host "In another terminal try: .\run_simulation.ps1 check   or   .\run_simulation.ps1 demo"
            Write-Host ""
            Invoke-InContainer "bash /project/scripts/sim_up.sh $launchArgs"; exit $LASTEXITCODE
        }
        "check"  { Assert-ContainerRunning; Invoke-InContainer "$RosEnv && ros2 run obstacle_bot sim_check"; exit $LASTEXITCODE }
        "demo"   { Assert-ContainerRunning; Invoke-InContainer "$RosEnv && ros2 run obstacle_bot drive_demo"; exit $LASTEXITCODE }
        "teleop" { Assert-ContainerRunning; Invoke-InContainer "$RosEnv && ros2 run turtlebot3_teleop teleop_keyboard"; exit $LASTEXITCODE }
        "shell"  { Assert-ContainerRunning; docker compose exec ros bash; exit $LASTEXITCODE }
        "build"  { Assert-ContainerRunning; Invoke-InContainer "bash /project/scripts/build.sh"; exit $LASTEXITCODE }
        "stop"   { Assert-ContainerRunning; Invoke-InContainer "bash /project/scripts/sim_down.sh"; exit $LASTEXITCODE }
        "down"   {
            if (Test-DockerReady) { docker compose down; Write-Host "Stopped. (Docker Desktop itself is still running; quit it from the tray to free all memory.)" }
            else { Write-Host "Docker isn't running; nothing to stop." }
        }
        "status" {
            if (-not (Test-DockerReady)) { Write-Host "Docker is not running."; break }
            docker compose ps
            if (Test-ContainerRunning) {
                Invoke-InContainer "$RosEnv && echo && echo ROS nodes: && ros2 node list"
            }
        }
        "help"   { Get-Help $PSCommandPath -Detailed }
    }
}
finally { Pop-Location }
