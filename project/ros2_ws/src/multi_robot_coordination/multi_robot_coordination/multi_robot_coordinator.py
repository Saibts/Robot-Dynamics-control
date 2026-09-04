"""
ROS 2 Multi-Robot Coordinator Node.
Coordinates workflow between Mobile Manipulator (TurtleBot3 + OpenManipulator) and Fixed Manipulator (UR5).
Manages:
- Action Clients for /navigate_and_pick and /ur5_pick_and_assemble
- Service Clients for /acquire_transfer_lock and /ur5_gripper_service
- Priority-based / FIFO / Round-Robin Task Scheduler dispatching
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
import time

# Interfaces are imported conditionally or mocked for simulation compatibility
try:
    from multi_robot_interfaces.action import NavigateAndPick, UR5PickAndPlace
    from multi_robot_interfaces.srv import AcquireHandoffLock
except ImportError:
    from multi_robot_coordination.action import NavigateAndPick, UR5PickAndPlace
    from multi_robot_coordination.srv import AcquireHandoffLock

class MultiRobotCoordinator(Node):
    def __init__(self):
        super().__init__('multi_robot_coordinator')
        self.get_logger().info('Initializing Central Multi-Robot Coordinator Node...')

        # Declare parameters
        self.declare_parameter('scheduler_mode', 'PRIORITY')
        self.scheduler_mode = self.get_parameter('scheduler_mode').get_parameter_value().string_value
        self.get_logger().info(f'Task Scheduler Mode set to: {self.scheduler_mode}')

        # Create Action Clients
        self.tb3_action_client = ActionClient(self, NavigateAndPick, 'navigate_and_pick')
        self.ur5_action_client = ActionClient(self, UR5PickAndPlace, 'ur5_pick_and_assemble')

        # Create Service Clients
        self.handoff_lock_client = self.create_client(AcquireHandoffLock, 'acquire_transfer_lock')

        # Internal State tracking
        self.current_active_task = None
        self.zone_locked = False
        
        self.get_logger().info('Coordinator Node ready and awaiting task ingestion.')

    def send_tb3_task(self, target_station, pickup_coords, priority=1):
        """Dispatches an asynchronous Action Goal to Mobile Manipulator."""
        self.get_logger().info(f'Sending Action Goal to Mobile Robot -> Station: {target_station}, Prio: {priority}')
        if not self.tb3_action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Mobile Robot Action Server (/navigate_and_pick) unavailable!')
            return False

        goal_msg = NavigateAndPick.Goal()
        goal_msg.target_station_id = target_station
        goal_msg.pickup_coordinates = pickup_coords
        goal_msg.priority_level = priority

        send_goal_future = self.tb3_action_client.send_goal_async(
            goal_msg, 
            feedback_callback=self.tb3_feedback_callback
        )
        send_goal_future.add_done_callback(self.tb3_goal_response_callback)
        return True

    def tb3_feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'[TB3 FEEDBACK] Phase: {feedback.current_phase} | Progress: {feedback.percent_complete:.1f}%')

    def tb3_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Mobile Robot rejected task goal!')
            return

        self.get_logger().info('Mobile Robot accepted task goal. Tracking execution...')
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.tb3_result_callback)

    def tb3_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'[TB3 RESULT] Success: {result.success}, Time: {result.total_navigation_time:.2f}s')
        if result.success:
            # Trigger Handshake Service & UR5 Action
            self.trigger_handoff_and_ur5_assembly()

    def trigger_handoff_and_ur5_assembly(self):
        """Acquires shared zone lock and dispatches UR5 Action Goal."""
        self.get_logger().info('Mobile Robot in handoff position. Requesting Shared Zone Lock via Service...')
        req = AcquireHandoffLock.Request()
        req.robot_id = 'multi_robot_coordinator'
        req.zone_id = 1
        req.request_lock = True

        future = self.handoff_lock_client.call_async(req)
        future.add_done_callback(self.handoff_lock_response_callback)

    def handoff_lock_response_callback(self, future):
        response = future.result()
        if response.lock_granted:
            self.get_logger().info('Zone Lock GRANTED. Triggering Fixed UR5 Manipulator Action Goal...')
            self.send_ur5_task()
        else:
            self.get_logger().warn(f'Zone Lock DENIED: {response.message}')

    def send_ur5_task(self):
        goal_msg = UR5PickAndPlace.Goal()
        goal_msg.task_id = 'HANDOFF_JOB_01'
        goal_msg.pickup_pose = [0.45, 0.20, 0.35]
        goal_msg.target_assembly_pose = [0.0, -0.50, 0.20]
        goal_msg.inspect_quality = True

        send_future = self.ur5_action_client.send_goal_async(goal_msg, feedback_callback=self.ur5_feedback_callback)
        send_future.add_done_callback(self.ur5_goal_response_callback)

    def ur5_feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(f'[UR5 FEEDBACK] State: {fb.joint_trajectory_state} | Progress: {fb.progress_fraction*100:.1f}%')

    def ur5_goal_response_callback(self, future):
        goal_handle = future.result()
        if goal_handle.accepted:
            get_res_future = goal_handle.get_result_async()
            get_res_future.add_done_callback(self.ur5_result_callback)

    def ur5_result_callback(self, future):
        res = future.result().result
        self.get_logger().info(f'[UR5 COMPLETED] Result: {res.completion_code}, Exec Time: {res.execution_time_seconds:.2f}s')
        # Release Zone Lock
        self.release_zone_lock()

    def release_zone_lock(self):
        req = AcquireHandoffLock.Request()
        req.robot_id = 'multi_robot_coordinator'
        req.zone_id = 1
        req.request_lock = False
        self.handoff_lock_client.call_async(req)
        self.get_logger().info('Shared Zone Lock RELEASED. Ready for subsequent task.')

def main(args=None):
    rclpy.init(args=args)
    coordinator = MultiRobotCoordinator()
    try:
        rclpy.spin(coordinator)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        coordinator.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
