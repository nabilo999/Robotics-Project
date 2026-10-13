"""Health check for the simulation: is the LiDAR publishing, and does the robot obey /cmd_vel?

Run (with the simulation already running):
    ros2 run obstacle_bot sim_check

Prints PASS/FAIL for each check and exits with code 0 only if everything passed.
The robot drives forward ~0.3 m and turns a little during the test.
"""
import math
import sys
import time

import rclpy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


def yaw_of(odom):
    q = odom.pose.pose.orientation
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class SimCheck(Node):
    def __init__(self):
        super().__init__("sim_check", parameter_overrides=[Parameter("use_sim_time", value=True)])
        self.scan = None
        self.scan_count = 0
        self.odom = None
        self.create_subscription(LaserScan, "/scan", self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Odometry, "/odom", self.on_odom, qos_profile_sensor_data)
        self.cmd_pub = self.create_publisher(TwistStamped, "/cmd_vel", 10)
        self.results = []

    def on_scan(self, msg):
        self.scan = msg
        self.scan_count += 1

    def on_odom(self, msg):
        self.odom = msg

    def record(self, name, ok, detail=""):
        self.results.append(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""), flush=True)

    def spin_until(self, condition, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
            if condition():
                return True
        return False

    def sim_now(self):
        return self.get_clock().now().nanoseconds / 1e9

    def drive(self, linear, angular, sim_seconds, wall_timeout=30.0):
        """Publish a velocity for `sim_seconds` of simulated time, then stop."""
        start = self.sim_now()
        end_wall = time.monotonic() + wall_timeout
        while self.sim_now() - start < sim_seconds and time.monotonic() < end_wall:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.twist.linear.x = float(linear)
            msg.twist.angular.z = float(angular)
            self.cmd_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.1)
        self.stop()

    def stop(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        self.cmd_pub.publish(msg)

    def settle(self, sim_seconds=1.0):
        start = self.sim_now()
        self.spin_until(lambda: self.sim_now() - start >= sim_seconds, timeout=15.0)

    def run(self):
        print("Simulation check (waiting up to 60 s for the simulator) ...", flush=True)

        # 1. LiDAR
        got_scan = self.spin_until(lambda: self.scan is not None, timeout=60.0)
        if got_scan:
            s = self.scan
            valid = [r for r in s.ranges if math.isfinite(r) and s.range_min <= r <= s.range_max]
            nearest = f"{min(valid):.2f} m" if valid else "nothing in range (empty world)"
            self.record("/scan is publishing LaserScan", True,
                        f"{len(s.ranges)} beams, {math.degrees(s.angle_max - s.angle_min):.0f} deg, "
                        f"range {s.range_min:.2f}-{s.range_max:.1f} m, frame '{s.header.frame_id}', "
                        f"nearest: {nearest}")
            count0, t0 = self.scan_count, time.monotonic()
            self.spin_until(lambda: False, timeout=3.0)
            rate = (self.scan_count - count0) / (time.monotonic() - t0)
            self.record("/scan rate", rate > 0.5, f"{rate:.1f} Hz (wall clock; LiDAR is 5 Hz in sim time)")
        else:
            self.record("/scan is publishing LaserScan", False, "no message in 60 s")

        # 2. Odometry and velocity topic
        got_odom = self.spin_until(lambda: self.odom is not None, timeout=20.0)
        self.record("/odom is publishing", got_odom)

        types = dict(self.get_topic_names_and_types())
        cmd_types = types.get("/cmd_vel", [])
        self.record("/cmd_vel uses geometry_msgs/msg/TwistStamped",
                    "geometry_msgs/msg/TwistStamped" in cmd_types, f"types: {cmd_types or 'topic missing'}")
        listeners = self.count_subscribers("/cmd_vel")
        self.record("simulator is listening on /cmd_vel", listeners > 0, f"{listeners} subscriber(s)")

        if not got_odom:
            return all(self.results)

        # 3. Movement: forward, then turn, then stop
        self.settle(0.5)
        p0 = self.odom.pose.pose.position
        x0, y0 = p0.x, p0.y
        self.drive(0.15, 0.0, 2.0)
        self.settle(1.0)
        p1 = self.odom.pose.pose.position
        moved = math.hypot(p1.x - x0, p1.y - y0)
        self.record("robot drives forward on /cmd_vel", moved > 0.05, f"moved {moved:.2f} m (expected ~0.3)")

        yaw0 = yaw_of(self.odom)
        self.drive(0.0, 0.5, 2.0)
        self.settle(1.0)
        turned = abs(math.atan2(math.sin(yaw_of(self.odom) - yaw0), math.cos(yaw_of(self.odom) - yaw0)))
        self.record("robot turns on /cmd_vel", turned > 0.2, f"turned {math.degrees(turned):.0f} deg (expected ~57)")

        twist = self.odom.twist.twist
        stopped = abs(twist.linear.x) < 0.02 and abs(twist.angular.z) < 0.05
        self.record("robot stops when commanded", stopped,
                    f"speed {twist.linear.x:.3f} m/s, {twist.angular.z:.3f} rad/s")
        return all(self.results)


def main(args=None):
    rclpy.init(args=args)
    node = SimCheck()
    ok = False
    try:
        ok = node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()
    print(("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED") + f" ({sum(node.results)}/{len(node.results)})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
