"""
Action Server for Fixed 6-DOF Manipulator (Universal Robots UR5).
Simulates MoveIt 2 trajectory planning, pick-and-place from mobile robot handoff platform, and assembly.
"""
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse

try:
    from multi_robot_interfaces.action import UR5PickAndPlace
except ImportError:
    from multi_robot_coordination.action import UR5PickAndPlace

class UR5ActionServer(Node):
    def __init__(self):
        super().__init__('ur5_action_server')
        self._action_server = ActionServer(
            self,
            UR5PickAndPlace,
            'ur5_pick_and_assemble',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback
        )
        self.get_logger().info('UR5 6-DOF Manipulator Action Server Started.')

    def goal_callback(self, goal_request):
        self.get_logger().info(f'Received UR5 Manipulation Task: {goal_request.task_id}')
        return GoalResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Planning & Executing UR5 MoveIt 2 Trajectory...')
        feedback_msg = UR5PickAndPlace.Feedback()

        # Phases: APPROACH -> GRASP -> RETRACT -> PLACE_AND_ASSEMBLE
        phases = [
            ('MOVEIT_APPROACHING_HANDOFF', 0.25),
            ('CLOSING_ROBOTIQ_GRIPPER', 0.50),
            ('CARTESIAN_LIFT_AND_RETRACT', 0.75),
            ('PRECISION_ASSEMBLY_INSERTION', 1.00)
        ]

        for phase_name, progress in phases:
            feedback_msg.joint_trajectory_state = phase_name
            feedback_msg.progress_fraction = progress
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(0.35)

        goal_handle.succeed()
        result = UR5PickAndPlace.Result()
        result.success = True
        result.completion_code = 'ASSEMBLY_SUCCESSFUL_INSPECTION_PASSED'
        result.execution_time_seconds = 1.4
        self.get_logger().info('UR5 Pick-and-Assemble Cycle Finished Successfully.')
        return result

def main(args=None):
    rclpy.init(args=args)
    node = UR5ActionServer()
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
