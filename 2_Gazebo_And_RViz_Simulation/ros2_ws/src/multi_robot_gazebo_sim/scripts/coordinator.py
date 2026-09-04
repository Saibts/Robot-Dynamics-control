"""
ROS 2 Multi-Robot Coordinator Node.
Coordinates workflow between Mobile Manipulator (TurtleBot3 + OpenManipulator) and Fixed Manipulator (UR5).
Manages:
- Action Clients for /navigate_and_pick and /ur5_pick_and_assemble
- Service Clients for /acquire_transfer_lock
- Priority-based / FIFO / Round-Robin Task Scheduler dispatching
- Dynamic task ingestion via /submit_task topic
"""
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String

try:
    from multi_robot_interfaces.action import NavigateAndPick, UR5PickAndPlace
    from multi_robot_interfaces.srv import AcquireHandoffLock
except ImportError:
    from multi_robot_coordination.action import NavigateAndPick, UR5PickAndPlace
    from multi_robot_coordination.srv import AcquireHandoffLock

try:
    from multi_robot_coordination.scheduler import Task, TaskScheduler
except ImportError:
    from scheduler import Task, TaskScheduler


class MultiRobotCoordinator(Node):
    def __init__(self):
        super().__init__('multi_robot_coordinator')
        self.get_logger().info('Initializing Central Multi-Robot Coordinator Node...')

        # Declare parameters
        self.declare_parameter('scheduler_mode', 'PRIORITY')
        self.declare_parameter('auto_demo_batch', False)

        self.scheduler_mode = self.get_parameter('scheduler_mode').get_parameter_value().string_value.upper()
        self.auto_demo_batch = self.get_parameter('auto_demo_batch').get_parameter_value().bool_value

        self.get_logger().info(f'Task Scheduler Mode set to: {self.scheduler_mode}')

        # Initialize Scheduler
        self.scheduler = TaskScheduler(mode=self.scheduler_mode)
        self.is_processing = False
        self.current_task = None
        self.completed_tasks = []

        # Create Action Clients
        self.tb3_action_client = ActionClient(self, NavigateAndPick, 'navigate_and_pick')
        self.ur5_action_client = ActionClient(self, UR5PickAndPlace, 'ur5_pick_and_assemble')

        # Create Service Clients
        self.handoff_lock_client = self.create_client(AcquireHandoffLock, 'acquire_transfer_lock')

        # Dynamic Task Ingestion Topic
        # Message format: "TASK_ID,PRIORITY,STATION"
        self.task_sub = self.create_subscription(
            String,
            '/submit_task',
            self.task_submission_callback,
            10
        )

        # Scheduler dispatch loop timer (checks for queued tasks every 0.5s)
        self.dispatch_timer = self.create_timer(0.5, self.check_and_dispatch_next_task)

        # Optional Auto Demo Batch timer (enqueues 3 demonstration tasks)
        if self.auto_demo_batch:
            self.demo_batch_timer = self.create_timer(2.0, self.enqueue_demo_batch)

        self.get_logger().info('=' * 70)
        self.get_logger().info(f'Coordinator Node ACTIVE | Scheduling Policy: {self.scheduler_mode}')
        self.get_logger().info('Send tasks via topic /submit_task (e.g. "TASK_01,1,STORAGE_STATION_B")')
        self.get_logger().info('=' * 70)

    def enqueue_demo_batch(self):
        # Fire once
        self.demo_batch_timer.cancel()
        self.get_logger().info('[DEMO] Ingesting initial demonstration batch of 3 tasks with staggered priorities:')
        # Task 1: Low Priority (3)
        self.add_task_to_scheduler('BATCH_TASK_A', priority=3, station='STORAGE_STATION_A')
        # Task 2: Urgent Priority (1)
        self.add_task_to_scheduler('BATCH_TASK_B_URGENT', priority=1, station='STORAGE_STATION_B')
        # Task 3: Medium Priority (2)
        self.add_task_to_scheduler('BATCH_TASK_C_HIGH', priority=2, station='STORAGE_STATION_A')
        self.get_logger().info(f'[DEMO] 3 tasks enqueued under {self.scheduler_mode} policy. Starting dispatch!')

    def task_submission_callback(self, msg):
        try:
            parts = [p.strip() for p in msg.data.split(',')]
            task_id = parts[0] if len(parts) > 0 and parts[0] else f'TASK_{len(self.completed_tasks)+1:02d}'
            priority = int(parts[1]) if len(parts) > 1 else 3
            station = parts[2] if len(parts) > 2 else 'STORAGE_STATION_B'
            self.add_task_to_scheduler(task_id, priority, station)
        except Exception as e:
            self.get_logger().error(f'Error parsing task message "{msg.data}": {e}')

    def add_task_to_scheduler(self, task_id, priority, station='STORAGE_STATION_B'):
        t = Task(task_id, priority, tb3_duration=10.0, ur5_duration=8.0, arrival_time=time.time())
        t.target_station = station
        self.scheduler.add_task(t)
        self.get_logger().info(f'[TASK ENQUEUED] ID: {task_id} | Prio: {priority} | Station: {station} | Mode: {self.scheduler_mode}')

    def check_and_dispatch_next_task(self):
        if not self.is_processing and self.scheduler.has_pending_tasks():
            self.current_task = self.scheduler.get_next_task()
            if not self.current_task:
                return

            self.is_processing = True
            wait_time = time.time() - self.current_task.arrival_time
            self.current_task.waiting_time = wait_time

            self.get_logger().info('=' * 65)
            self.get_logger().info(f'>>> [SCHEDULER DISPATCH] Policy: {self.scheduler_mode}')
            self.get_logger().info(f'>>> Selected Task: {self.current_task.task_id} (Priority: {self.current_task.priority})')
            self.get_logger().info(f'>>> In-Queue Wait Time: {wait_time:.2f}s')
            self.get_logger().info('=' * 65)

            station = getattr(self.current_task, 'target_station', 'STORAGE_STATION_B')
            self.send_tb3_task(station, [1.45, 1.20, 0.25], priority=self.current_task.priority)

    def send_tb3_task(self, target_station, pickup_coords, priority=1):
        if not self.tb3_action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Mobile Robot Action Server (/navigate_and_pick) unavailable!')
            self.is_processing = False
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
            self.is_processing = False
            return

        self.get_logger().info('Mobile Robot accepted task goal. Tracking execution in RViz...')
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.tb3_result_callback)

    def tb3_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'[TB3 RESULT] Success: {result.success}, Navigation Time: {result.total_navigation_time:.2f}s')
        if result.success:
            self.trigger_handoff_and_ur5_assembly()
        else:
            self.is_processing = False

    def trigger_handoff_and_ur5_assembly(self):
        self.get_logger().info('TB3 Docked. Requesting Transfer Zone Mutex Lock via Service...')
        req = AcquireHandoffLock.Request()
        req.robot_id = 'multi_robot_coordinator'
        req.zone_id = 1
        req.request_lock = True

        future = self.handoff_lock_client.call_async(req)
        future.add_done_callback(self.handoff_lock_response_callback)

    def handoff_lock_response_callback(self, future):
        response = future.result()
        if response.lock_granted:
            self.get_logger().info('[MUTEX GRANTED] Transfer Zone secured. Dispatching UR5 Action Goal...')
            self.send_ur5_task()
        else:
            self.get_logger().warn(f'[MUTEX DENIED] {response.message}')
            self.is_processing = False

    def send_ur5_task(self):
        goal_msg = UR5PickAndPlace.Goal()
        goal_msg.task_id = self.current_task.task_id if self.current_task else 'TASK_HANDOFF'
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
        else:
            self.get_logger().warn('UR5 rejected task goal!')
            self.release_zone_lock()

    def ur5_result_callback(self, future):
        res = future.result().result
        self.get_logger().info(f'[UR5 COMPLETED] Result: {res.completion_code}, Exec Time: {res.execution_time_seconds:.2f}s')
        if self.current_task:
            self.completed_tasks.append(self.current_task)
            self.get_logger().info(f'[TASK COMPLETED] Finished {self.current_task.task_id}. Total Completed: {len(self.completed_tasks)}')
        self.release_zone_lock()

    def release_zone_lock(self):
        req = AcquireHandoffLock.Request()
        req.robot_id = 'multi_robot_coordinator'
        req.zone_id = 1
        req.request_lock = False
        future = self.handoff_lock_client.call_async(req)
        future.add_done_callback(self.zone_released_callback)

    def zone_released_callback(self, future):
        self.get_logger().info('Shared Zone Mutex Lock RELEASED. Coordinator ready for next task.')
        self.is_processing = False
        self.current_task = None
        self.check_and_dispatch_next_task()


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
