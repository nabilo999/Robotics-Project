# Robotics Group Project: TurtleBot3 Simulation

A simulated **TurtleBot3 Burger** (a small round robot with 2 wheels and a 360° LiDAR) in an empty **Gazebo** world, using **ROS 2 Jazzy**. Everything runs in Docker, reusing the course's `robotics-fall2026:jazzy` image. You view it in your browser at **http://localhost:6081**.

## Quick start

Double-click **`1 - Start Simulation.bat`**. It starts Docker, starts Gazebo and the robot, and opens the browser. Gazebo appears in about 30–60 s. Keep the black window open; closing it or pressing Ctrl+C stops the sim.

## Which file do I use?

| I want to… | Use |
|---|---|
| Start the simulation | `1 - Start Simulation.bat` |
| Start it with RViz (shows LiDAR points; slower) | `1b - Start Simulation with RViz.bat` |
| Check that LiDAR and driving work | `2 - Check Robot.bat` (prints PASS/FAIL) |
| See the robot drive forward, turn, drive forward | `3 - Drive Demo.bat` |
| Drive with the keyboard (w/x speed, a/d turn, s stop) | `4 - Keyboard Drive.bat` |
| Stop everything and free memory | `5 - Stop Simulation.bat` |
| Same things from a terminal | `.\run_simulation.ps1 start\|check\|demo\|teleop\|shell\|stop\|down\|status` (bash: `./run_simulation.sh`) |
| Write robot code (obstacle avoidance goes here) | `ros2_ws/src/obstacle_bot/obstacle_bot/` (example: `drive_demo.py`) |
| Register a new program as a command | `ros2_ws/src/obstacle_bot/setup.py` → `console_scripts` |
| Change what starts with the sim | `ros2_ws/src/obstacle_bot/launch/sim.launch.py` |
| Make a world with obstacles | copy `ros2_ws/src/obstacle_bot/worlds/empty.sdf` and add `<model>` blocks |
| Docker settings (image, port) | `compose.yaml` |
| Helper scripts that run inside the container | `scripts/` |

Code changes are picked up automatically: every start rebuilds the workspace.

## Folder layout
```
Robotics Project/
├── *.bat                     double-click shortcuts (see table)
├── run_simulation.ps1 / .sh  the launcher everything goes through
├── compose.yaml              Docker container definition
├── scripts/                  run inside the container (build, start/stop sim, env setup)
└── ros2_ws/src/obstacle_bot/ our ROS 2 package
    ├── launch/sim.launch.py  Gazebo + robot (+ optional RViz)
    ├── worlds/empty.sdf      floor + light
    └── obstacle_bot/         Python nodes: drive_demo.py, sim_check.py
```

## Robot interface (what your code talks to)

| Topic | Type | Meaning |
|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | LiDAR: 360 beams (index 0 = straight ahead, counter-clockwise, 1° each), 0.12–3.5 m, `inf` = nothing hit, 5 Hz |
| `/cmd_vel` | **`geometry_msgs/TwistStamped`** | drive: `twist.linear.x` m/s (max ~0.22), `twist.angular.z` rad/s (+ = left) |
| `/odom` | `nav_msgs/Odometry` | robot position and heading |
| `/tf`, `/clock`, `/imu`, `/joint_states` | | frames, sim time, IMU, wheels |

⚠️ On ROS 2 Jazzy, `/cmd_vel` is **TwistStamped**, not `Twist`. Publishing a plain `Twist` does nothing.

Manual test from `.\run_simulation.ps1 shell`:
```bash
ros2 topic echo /scan --once
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.1}}}"   # Ctrl+C, then the robot coasts to a stop
```

## How it works
- The launcher starts Docker Desktop if needed, then runs `docker compose up` (container `robotics-project-ros-1`, project folder mounted at `/project`). After that it runs `scripts/sim_up.sh` in the container.
- `sim_up.sh` cleans up any old sim, builds `ros2_ws` with colcon, and runs `ros2 launch obstacle_bot sim.launch.py`.
- `sim.launch.py` reuses TurtleBot3's own launch files (`robot_state_publisher`, spawn and `ros_gz_bridge`) and the course image's packages. It adds our world (the floor is built in, so no internet download) and a close-up camera view.
- Gazebo and RViz windows are shown through a virtual desktop in the browser (noVNC) on port 6081. The course uses 6080, so the two don't clash.
- Launch options: `rviz:=true`, `gui:=false` (no Gazebo window), `world:=<file.sdf>`, `x_pose:=`, `y_pose:=`.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Docker did not start" | Open Docker Desktop. If it shows an error or update dialog, close or skip it. **Never pick "Reset to factory defaults" or "Clean/Purge data"**: that deletes the ROS image, and rebuilding it needs ~12 GB of free disk. |
| "image robotics-fall2026:jazzy not found" | Build it once in the course repo: `cd ...\robotics-fall2026; docker compose build` |
| Browser shows "Connecting…" or nothing | Wait 10 s and reload `http://localhost:6081/vnc.html?autoconnect=1&resize=scale` |
| Gazebo window grey/empty or very slow | Software rendering on this laptop is slow (Gazebo ~0.7× real time, ~0.4× with RViz too). Close other apps, or use `start -NoGui -RViz`. |
| Robot doesn't move | Is the sim running? Run `2 - Check Robot.bat`. Make sure your code publishes **TwistStamped** on `/cmd_vel`. |
| Weird leftovers after closing the window | `5 - Stop Simulation.bat`, then start again. |
| Course container also running | Stop it to save RAM: `.\scripts\ros_course.ps1 stop` in the course repo. |
| `.sh` script fails with `$'\r'` errors | The file got Windows line endings. Re-save it as LF; `.gitattributes` prevents this once you use git. |

## Verified (2026-10-12, on this laptop)
- Cold start through the launcher: Gazebo opens with the floor and the robot, and the robot appears in the browser.
- `check`: 8/8 PASS. `/scan` publishes 360 beams; the robot drove 0.29 m, turned 57° and stopped via `/cmd_vel`.
- `demo`: the robot drove, turned about 90° (odometry heading 57° → 149°), drove and stopped.
- RViz shows the robot, TF and LiDAR points. A test box placed 1 m ahead was seen at 0.90 m.
- `stop` leaves no Gazebo processes behind; `down` removes the container.
- Not tested: `4 - Keyboard Drive` (needs a human at the keyboard) and `run_simulation.sh` under Git Bash.
