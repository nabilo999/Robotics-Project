import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import LaserScan


class SecurityRobot(Node):
    def __init__(self):
        super().__init__('security_robot')

        # Send movement commands to the robot
        self.publisher = self.create_publisher(TwistStamped, '/cmd_vel', 10)

        # Receive LiDAR measurements
        self.subscription = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)

        # Store the distances detected by the LiDAR
        self.front_distance = None
        self.left_distance = None
        self.right_distance = None

        # Check what the robot should do every 0.1 seconds
        self.timer = self.create_timer(0.1, self.move_robot)

    def scan_callback(self, msg):
        # Divide the LiDAR readings into front, left, and right
        front = []
        left = []
        right = []

        for i, distance in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment

            # Ignore invalid or out-of-range measurements
            if not math.isfinite(distance):
                continue
            if distance < msg.range_min or distance > msg.range_max:
                continue

            # Convert the angle to a value between -pi and pi
            angle = math.atan2(math.sin(angle), math.cos(angle))

            if -math.pi / 4 <= angle <= math.pi / 4:
                front.append(distance)
            elif math.pi / 4 < angle <= 3 * math.pi / 4:
                left.append(distance)
            elif -3 * math.pi / 4 <= angle < -math.pi / 4:
                right.append(distance)

        # Save the closest object in each direction
        self.front_distance = min(front, default=float('inf'))
        self.left_distance = min(left, default=float('inf'))
        self.right_distance = min(right, default=float('inf'))

    def move_robot(self):
        # Create a movement command
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        # waits until the first LiDAR measurement arrives
        if self.front_distance is None:
            self.publisher.publish(msg)
            return

        # If an object is too close, turn toward the clearer side
        if self.front_distance < 0.7:
            msg.twist.linear.x = 0.0

            if self.left_distance >= self.right_distance:
                msg.twist.angular.z = 0.5  # Turn left
            else:
                msg.twist.angular.z = -0.5  # Turn right

        # If the path is clear, move forward
        else:
            msg.twist.linear.x = 0.15
            msg.twist.angular.z = 0.0

        # Send the command to the robot
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SecurityRobot()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the robot when the program ends
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        node.publisher.publish(msg)

        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
