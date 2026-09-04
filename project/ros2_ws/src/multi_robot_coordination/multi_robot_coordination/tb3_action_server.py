"""
Action Server for Mobile Manipulator (TurtleBot3 + OpenManipulator-X).
Simulates long-running navigation and 4-DOF manipulator pick operation with continuous feedback.
"""
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse

try:
    from multi_robot_interfaces.action import NavigateAndPick
except ImportError:
    from multi_robot_coordination.action import NavigateAndPick

class TurtleBot3ActionServer(Node):
    def __init__(self):
        super().__init__('tb3_action_server')
        self._action_server = ActionServer(
            self,
            NavigateAndPick,
            'navigate_and_pick',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )
        self.get_logger().info('TurtleBot3 Mobile Manipulator Action Server Started.')

    def goal_callback(self, goal_request):
        self.get_logger().info(f'Received Goal for Station: {goal_request.target_station_id}')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().warn('Received request to cancel Mobile Robot Action Goal!')
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing Navigate & Pick action sequence...')
        feedback_msg = NavigateAndPick.Feedback()

        # Step 1: Nav2 Navigation (0% to 50%)
        feedback_msg.current_phase = 'NAVIGATING_TO_PICKUP'
        for i in range(1, 6):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Action Goal successfully canceled.')
                result = NavigateAndPick.Result()
                result.success = False
                result.status_message = 'Goal Canceled'
                return result

            feedback_msg.percent_complete = float(i * 10)
            feedback_msg.current_pose_x = 0.5 * i
            feedback_msg.current_pose_y = 0.3 * i
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(0.4)

        # Step 2: OpenManipulator Arm Pick (50% to 100%)
        feedback_msg.current_phase = 'OPENMANIPULATOR_GRASPING'
        for i in range(6, 11):
            feedback_msg.percent_complete = float(i * 10)
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(0.3)

        goal_handle.succeed()
        result = NavigateAndPick.Result()
        result.success = True
        result.status_message = 'Part successfully retrieved and transported to handoff zone.'
        result.total_navigation_time = 3.5
        self.get_logger().info('Mobile Robot Action Goal Succeeded!')
        return result

def main(args=None):
    rclpy.init(args=args)
    node = TurtleBot3ActionServer()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
