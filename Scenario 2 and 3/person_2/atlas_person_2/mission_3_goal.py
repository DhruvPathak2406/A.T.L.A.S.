from atlas_person_2.goal_common import MissionGoal
import rclpy


def main(args=None):
    rclpy.init(args=args)
    node = MissionGoal('mission_3_goal')
    try:
        success = node.execute()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    if not success:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
