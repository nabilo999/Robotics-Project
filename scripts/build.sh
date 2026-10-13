#!/usr/bin/env bash
# Build the project's ROS 2 workspace (runs inside the container).
set -eo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

source /opt/ros/jazzy/setup.bash
cd "$PROJECT_ROOT/ros2_ws"
# --symlink-install: edits to Python files take effect without rebuilding.
colcon build --symlink-install
