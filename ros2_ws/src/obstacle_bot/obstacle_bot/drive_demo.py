"""Drive demo: forward, turn left ~90 degrees, forward, stop.

Run (with the simulation already running):
    ros2 run obstacle_bot drive_demo

How driving works: publish geometry_msgs/TwistStamped on /cmd_vel.
  twist.linear.x  = forward speed in m/s     (Burger max ~0.22)
  twist.angular.z = turn speed in rad/s      (positive = left / counter-clockwise)
On ROS 2 Jazzy the TurtleBot3 Gazebo bridge expects TwistStamped, not plain Twist.
"""
import math

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from rclpy.parameter import Parameter

FORWARD_SPEED = 0.15  # m/s
TURN_SPEED = 0.5      # rad/s

# (description, linear m/s, angular rad/s, duration in simulated seconds)
STEPS = [
    ("forward", FORWARD_SPEED, 0.0, 3.0),
    ("turn left 90 degrees", 0.0, TURN_SPEED, (math.pi / 2) / TURN_SPEED),
    ("forward", FORWARD_SPEED, 0.0, 3.0),
    ("stop", 0.0, 0.0, 0.5),
]


class DriveDemo(Node):
    def __init__(self):
        # Use Gazebo's clock so durations are correct even if the simulation runs slower than real time.
        super().__init__("drive_demo", parameter_overrides=[Parameter("use_sim_time", value=True)])
        self.pub = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        self.step = -1
        self.step_end = None
        self.done = False
        self.create_timer(0.1, self.tick)  # 10 Hz
        self.get_logger().info("Waiting for the simulator (/cmd_vel subscriber and /clock) ...")

    def send(self, linear, angular):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x = float(linear)
        msg.twist.angular.z = float(angular)
        self.pub.publish(msg)

    def tick(self):
        now = self.get_clock().now().nanoseconds / 1e9
        if now == 0.0 or self.pub.get_subscription_count() == 0:
            return  # simulator not up yet
        if self.step_end is None or now >= self.step_end:
            self.step += 1
            if self.step >= len(STEPS):
                self.send(0.0, 0.0)
                self.get_logger().info("Demo finished.")
                self.done = True
                return
            name, _, _, duration = STEPS[self.step]
            self.step_end = now + duration
            self.get_logger().info(f"Step {self.step + 1}/{len(STEPS)}: {name} ({duration:.1f} s)")
        _, linear, angular, _ = STEPS[self.step]
        self.send(linear, angular)


def main(args=None):
    rclpy.init(args=args)
    node = DriveDemo()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.send(0.0, 0.0)  # never leave the robot driving
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    main()
