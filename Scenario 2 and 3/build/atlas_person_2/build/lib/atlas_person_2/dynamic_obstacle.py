import math

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node


def _parse_waypoints(value):
    try:
        points = [
            tuple(float(coordinate.strip()) for coordinate in point.split(','))
            for point in value.split(';')
        ]
    except ValueError as error:
        raise ValueError('waypoints must be semicolon-separated x,y pairs') from error
    if len(points) < 2 or any(len(point) != 2 for point in points):
        raise ValueError('waypoints must contain at least two x,y pairs')
    if any(not all(math.isfinite(coordinate) for coordinate in point) for point in points):
        raise ValueError('waypoint coordinates must be finite')
    if any(math.dist(points[index], points[index + 1]) < 0.1
           for index in range(len(points) - 1)):
        raise ValueError('consecutive waypoints must be at least 0.1 m apart')
    return points


class DynamicObstacle(Node):
    def __init__(self):
        super().__init__('dynamic_obstacle')
        self.declare_parameter('speed', 0.22)
        self.declare_parameter(
            'waypoints', '-0.2,-1.7;-0.2,1.7;0.4,1.7;0.4,-1.7')
        speed = float(self.get_parameter('speed').value)
        if not math.isfinite(speed) or not 0.05 <= speed <= 0.5:
            raise ValueError('speed must be between 0.05 and 0.5 m/s')
        self.speed = speed
        self.waypoints = _parse_waypoints(str(self.get_parameter('waypoints').value))
        self.x, self.y = self.waypoints[0]
        self.yaw = 0.0
        self.target_index = 1
        self.previous_time = self.get_clock().now()
        self.publisher = self.create_publisher(Twist, '/hazard/cmd_vel', 10)
        self.timer = self.create_timer(0.05, self._step)
        self.get_logger().info(
            f'Moving hazard following {len(self.waypoints)} waypoints at '
            f'{self.speed:.2f} m/s.')

    def _step(self):
        now = self.get_clock().now()
        dt = (now - self.previous_time).nanoseconds / 1e9
        self.previous_time = now
        if dt <= 0.0 or dt > 0.25:
            self._publish_stop()
            return

        target_x, target_y = self.waypoints[self.target_index]
        dx, dy = target_x - self.x, target_y - self.y
        distance = math.hypot(dx, dy)
        if distance < 0.15:
            self.target_index = (self.target_index + 1) % len(self.waypoints)
            return

        target_yaw = math.atan2(dy, dx)
        error = math.atan2(
            math.sin(target_yaw - self.yaw),
            math.cos(target_yaw - self.yaw))
        command = Twist()
        command.angular.z = max(-1.0, min(1.0, 2.0 * error))
        if abs(error) < 0.55:
            command.linear.x = self.speed * max(0.25, math.cos(error))
        self.publisher.publish(command)
        self.yaw = math.atan2(
            math.sin(self.yaw + command.angular.z * dt),
            math.cos(self.yaw + command.angular.z * dt))
        self.x += command.linear.x * math.cos(self.yaw) * dt
        self.y += command.linear.x * math.sin(self.yaw) * dt

    def _publish_stop(self):
        self.publisher.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = DynamicObstacle()
    try:
        rclpy.spin(node)
    finally:
        node._publish_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
