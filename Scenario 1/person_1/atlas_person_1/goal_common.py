import math
import time

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener


class MissionGoal(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.declare_parameter('goal_x', 0.0)
        self.declare_parameter('goal_y', 0.0)
        self.declare_parameter('goal_yaw', 0.0)
        self.action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def execute(self):
        if not self.action_client.wait_for_server(timeout_sec=180.0):
            self.get_logger().error('Nav2 NavigateToPose action server was not available.')
            return False

        deadline = time.monotonic() + 90.0
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.tf_buffer.can_transform(
                    'map', 'base_footprint', Time(),
                    timeout=Duration(seconds=0.05)):
                break
        else:
            self.get_logger().error(
                'No map-to-base transform became available; SLAM/localization is not ready.')
            return False

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.pose.position.x = float(self.get_parameter('goal_x').value)
        goal.pose.pose.position.y = float(self.get_parameter('goal_y').value)
        yaw = float(self.get_parameter('goal_yaw').value)
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.get_logger().info(
            f'Sending navigation goal ({goal.pose.pose.position.x:.2f}, '
            f'{goal.pose.pose.position.y:.2f}) in map.')
        goal_handle = None
        accept_deadline = time.monotonic() + 180.0
        while rclpy.ok() and time.monotonic() < accept_deadline:
            send_future = self.action_client.send_goal_async(
                goal, feedback_callback=self._feedback)
            rclpy.spin_until_future_complete(self, send_future)
            candidate = send_future.result()
            if candidate is not None and candidate.accepted:
                goal_handle = candidate
                break
            self.get_logger().info(
                'Nav2 is not active yet; retrying the mission goal shortly.')
            rclpy.spin_once(self, timeout_sec=1.0)
        if goal_handle is None:
            self.get_logger().error('Nav2 did not accept the mission goal in time.')
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        wrapped_result = result_future.result()
        if wrapped_result is None:
            self.get_logger().error('Navigation ended without an action result.')
            return False
        if wrapped_result.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Mission goal reached successfully.')
            return True

        self.get_logger().error(
            f'Navigation failed with action status {wrapped_result.status}; '
            f'Nav2 result: {wrapped_result.result}.')
        return False

    def _feedback(self, message):
        feedback = message.feedback
        self.get_logger().info(
            f'Distance remaining: {feedback.distance_remaining:.2f} m',
            throttle_duration_sec=5.0)
