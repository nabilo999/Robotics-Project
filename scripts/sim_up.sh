#!/usr/bin/env bash
# Build the workspace and start Gazebo + TurtleBot3 Burger (runs inside the container).
# Extra arguments are passed to the launch file, e.g.:  sim_up.sh rviz:=true
set -eo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Clear out any simulation left over from a previous run.
bash "$PROJECT_ROOT/scripts/sim_down.sh" --quiet

echo "==> Building ros2_ws ..."
bash "$PROJECT_ROOT/scripts/build.sh" > /tmp/obstacle_bot_build.log 2>&1 || {
  cat /tmp/obstacle_bot_build.log
  echo "Build failed (log above)."
  exit 1
}

source "$PROJECT_ROOT/scripts/project_env.sh"

# Whatever happens (Ctrl+C, crash), don't leave Gazebo running.
trap 'bash "$PROJECT_ROOT/scripts/sim_down.sh" --quiet' EXIT

echo "==> Launching Gazebo with the TurtleBot3 Burger (first start can take ~1 minute) ..."
ros2 launch obstacle_bot sim.launch.py "$@"
