# Source this file (don't run it) to load ROS 2 and this project's workspace:
#   source /project/scripts/project_env.sh
# Every terminal inside the container does this automatically.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROJECT_ROOT

source /opt/ros/jazzy/setup.bash
if [[ -f "$PROJECT_ROOT/ros2_ws/install/setup.bash" ]]; then
  source "$PROJECT_ROOT/ros2_ws/install/setup.bash"
fi

export TURTLEBOT3_MODEL=burger
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
