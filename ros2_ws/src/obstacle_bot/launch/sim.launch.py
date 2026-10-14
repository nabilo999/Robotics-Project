"""Start Gazebo, spawn the TurtleBot3 Burger (2 wheels + 360-degree LiDAR), optionally RViz.

    ros2 launch obstacle_bot sim.launch.py                 # Gazebo window + robot
    ros2 launch obstacle_bot sim.launch.py rviz:=true      # also open RViz
    ros2 launch obstacle_bot sim.launch.py gui:=false      # no Gazebo window (saves CPU/RAM)
    ros2 launch obstacle_bot sim.launch.py world:=/project/ros2_ws/src/obstacle_bot/worlds/my.sdf

This is the same recipe as turtlebot3_gazebo's empty_world.launch.py (Gazebo server +
client, robot_state_publisher, spawn + ros_gz_bridge), reusing its sub-launch files,
but with our own world file and on/off switches for the GUI and RViz.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument, ExecuteProcess,
                            IncludeLaunchDescription, SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    this_pkg = get_package_share_directory("obstacle_bot")
    tb3_gazebo = get_package_share_directory("turtlebot3_gazebo")
    tb3_launch = os.path.join(tb3_gazebo, "launch")
    gz_sim_launch = os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")

    world = LaunchConfiguration("world")
    gui = LaunchConfiguration("gui")
    rviz = LaunchConfiguration("rviz")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")

    return LaunchDescription([
        DeclareLaunchArgument("world",
            default_value="/project/ros2_ws/src/obstacle_bot/worlds/hallway.sdf",
            description="Gazebo world (.sdf) to load",),
        DeclareLaunchArgument("gui", default_value="true", description="Open the Gazebo window"),
        DeclareLaunchArgument("rviz", default_value="false", description="Open RViz"),
        DeclareLaunchArgument("x_pose", default_value="0.0", description="Robot start x (m)"),
        DeclareLaunchArgument("y_pose", default_value="0.0", description="Robot start y (m)"),

        # The TurtleBot3 launch files read the robot model from this variable.
        SetEnvironmentVariable("TURTLEBOT3_MODEL", "burger"),
        # Lets Gazebo find the TurtleBot3 meshes.
        AppendEnvironmentVariable("GZ_SIM_RESOURCE_PATH", os.path.join(tb3_gazebo, "models")),

        # Gazebo physics server (-r: start running immediately, -s: server only).
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_sim_launch),
            launch_arguments={"gz_args": ["-r -s -v2 ", world], "on_exit_shutdown": "true"}.items(),
        ),
        # Gazebo window (-g: GUI only).
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_sim_launch),
            launch_arguments={"gz_args": "-g -v2 "}.items(),
            condition=IfCondition(gui),
        ),
        # Publishes the robot's frames (base_footprint, base_link, base_scan, wheels) on /tf.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(tb3_launch, "robot_state_publisher.launch.py")),
            launch_arguments={"use_sim_time": "true"}.items(),
        ),
        # Spawns the robot and starts ros_gz_bridge (/scan, /odom, /cmd_vel, /tf, /imu, /clock).
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(tb3_launch, "spawn_turtlebot3.launch.py")),
            launch_arguments={"x_pose": x_pose, "y_pose": y_pose}.items(),
        ),
        # Once the Gazebo window is up, move its camera close to the robot (default view is ~8 m away).
        ExecuteProcess(
            cmd=["bash", "-c",
                 "for i in $(seq 90); do gz service -l 2>/dev/null | grep -q /gui/move_to/pose && break; sleep 1; done; "
                 "sleep 2; gz service -s /gui/move_to/pose --reqtype gz.msgs.GUICamera --reptype gz.msgs.Boolean "
                 "--timeout 3000 --req 'pose: {position: {x: -1.0, y: -0.6, z: 0.7}, "
                 "orientation: {x: -0.0711, y: 0.2570, z: 0.2570, w: 0.9289}}' > /dev/null"],
            condition=IfCondition(gui),
        ),
        Node(
            package="rviz2", executable="rviz2", name="rviz2", output="screen",
            arguments=["-d", os.path.join(tb3_gazebo, "rviz", "tb3_gazebo.rviz")],
            parameters=[{"use_sim_time": True}],
            condition=IfCondition(rviz),
        ),
    ])
