from glob import glob

from setuptools import find_packages, setup

package_name = "obstacle_bot"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/worlds", glob("worlds/*.sdf")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Robotics group project",
    maintainer_email="nabil.said@codepath.org",
    description="Simulated TurtleBot3 Burger in Gazebo (foundation for LiDAR obstacle avoidance).",
    license="MIT",
    entry_points={
        "console_scripts": [
            "drive_demo = obstacle_bot.drive_demo:main",
            "sim_check = obstacle_bot.sim_check:main",
            "obstacle_avoidance = obstacle_bot.obstacle_avoidance:main",
        ],
    },
)
