#!/usr/bin/env bash
# One-command launcher (bash version, for Linux/macOS or Git Bash). On Windows the
# PowerShell version (run_simulation.ps1 / the .bat files) is the main one.
#
#   ./run_simulation.sh [start|check|demo|teleop|shell|stop|down|status|build] [--rviz] [--no-gui]
set -eo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export MSYS_NO_PATHCONV=1   # stop Git Bash from rewriting /project/... paths

IMAGE="${COURSE_ROS_IMAGE:-robotics-fall2026:jazzy}"
DESKTOP_URL="http://localhost:6081/vnc.html?autoconnect=1&resize=scale"
ROS_ENV="source /project/scripts/project_env.sh"

cmd="${1:-start}"; shift || true
rviz=false; gui=true
for arg in "$@"; do
  case "$arg" in
    --rviz) rviz=true ;;
    --no-gui) gui=false ;;
    *) echo "Unknown option: $arg"; exit 2 ;;
  esac
done

die() { echo "ERROR: $*" >&2; exit 1; }
running() { [[ -n "$(docker compose ps -q --status running ros 2>/dev/null)" ]]; }
in_container() {
  local tty=(); [[ -t 0 && -t 1 ]] || tty=(-T)
  docker compose exec "${tty[@]}" ros bash -lc "$1"
}
need_running() { docker info >/dev/null 2>&1 && running || die "Simulation container isn't running. Start it: ./run_simulation.sh start"; }

case "$cmd" in
  start)
    command -v docker >/dev/null || die "Docker is not installed."
    docker info >/dev/null 2>&1 || die "Docker isn't running. Start Docker Desktop (close any dialog it shows) and retry."
    docker image inspect "$IMAGE" >/dev/null 2>&1 || die "Image $IMAGE not found. Build it once in the course repo: docker compose build"
    running || docker compose up -d
    echo
    echo "Simulation desktop: $DESKTOP_URL"
    echo "Gazebo appears there in ~30-60 s. Press Ctrl+C here to stop."
    echo
    in_container "bash /project/scripts/sim_up.sh rviz:=$rviz gui:=$gui"
    ;;
  check)  need_running; in_container "$ROS_ENV && ros2 run obstacle_bot sim_check" ;;
  demo)   need_running; in_container "$ROS_ENV && ros2 run obstacle_bot drive_demo" ;;
  teleop) need_running; in_container "$ROS_ENV && ros2 run turtlebot3_teleop teleop_keyboard" ;;
  shell)  need_running; docker compose exec ros bash ;;
  build)  need_running; in_container "bash /project/scripts/build.sh" ;;
  stop)   need_running; in_container "bash /project/scripts/sim_down.sh" ;;
  down)   docker compose down ;;
  status) docker compose ps; running && in_container "$ROS_ENV && echo && echo ROS nodes: && ros2 node list" ;;
  *) echo "Usage: $0 [start|check|demo|teleop|shell|stop|down|status|build] [--rviz] [--no-gui]"; exit 2 ;;
esac
