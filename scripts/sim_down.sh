#!/usr/bin/env bash
# Stop the simulation and anything it left behind (runs inside the container).
# Gazebo sometimes keeps running after its launch file exits, so we clean up by name.

# Ask the launch file to shut down cleanly first.
pkill -INT -f "ros2 launch obstacle_bot" 2>/dev/null && sleep 3

for pattern in "drive_demo" "sim_check" "teleop_keyboard" "rviz2" \
               "parameter_bridge" "robot_state_publisher" "ros_gz_sim" "gz sim"; do
  pkill -f "$pattern" 2>/dev/null
done
sleep 1
pkill -9 -f "gz sim" 2>/dev/null

if [[ "${1:-}" != "--quiet" ]]; then
  echo "Simulation stopped."
fi
exit 0
