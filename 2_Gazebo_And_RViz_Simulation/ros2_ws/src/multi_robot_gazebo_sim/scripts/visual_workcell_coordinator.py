#!/usr/bin/env python3
"""
Action-Driven Visual Workcell Coordinator with DYNAMIC WORKPIECE PICK & PLACE.
Directly implements Topic 3 Architecture:
1. Action Server: /navigate_and_pick (multi_robot_interfaces/action/NavigateAndPick)
2. Action Server: /ur5_pick_and_assemble (multi_robot_interfaces/action/UR5PickAndPlace)
3. Service Server: /acquire_transfer_lock (multi_robot_interfaces/srv/AcquireHandoffLock)
4. JointState Publisher: /joint_states at 30 Hz (Smooth kinematic visualization & articulation)
5. Dynamic Workpiece Publisher: /workcell/workpiece_marker (Physical pick & place!)
6. Floating Status Badge: /workcell/status_text_marker
"""

import math
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from visualization_msgs.msg import Marker

from multi_robot_interfaces.action import NavigateAndPick, UR5PickAndPlace
from multi_robot_interfaces.srv import AcquireHandoffLock


# -----------------------------------------------------------------------------
# Smooth Cosine Interpolation Helpers
# -----------------------------------------------------------------------------
def smooth_step(p):
    """Cosine S-curve with zero velocity and zero acceleration at boundaries."""
    p = max(0.0, min(1.0, p))
    return 0.5 * (1.0 - math.cos(p * math.pi))


def lerp(a, b, s):
    """Vector linear interpolation using smoothed progress s."""
    return [a[i] + (b[i] - a[i]) * s for i in range(len(a))]


# -----------------------------------------------------------------------------
# Calibrated Robotic Poses (URDF Kinematic Solutions - Flange Normal along -Z)
# -----------------------------------------------------------------------------
# UR5: [shoulder_pan, shoulder_lift, elbow, wrist_1, wrist_2, wrist_3]
UR5_HOME        = [-0.8055, -0.9535,  1.9567,  0.5677,  1.5708,  0.0000]  # Elevated Home Staging (TCP Z = 0.55m, pointing down)
UR5_DOCK_HOVER  = [-0.2319, -0.5526,  1.3375,  0.7859,  1.5708,  0.0000]  # Above Yellow Dock Pad (TCP Z = 0.48m, pointing down)
UR5_DOCK_GRASP  = [-0.2319, -0.1985,  1.1659,  0.6034,  1.5708,  0.0000]  # Precision Descent onto Part (TCP Z = 0.295m, pointing down)
UR5_DOCK_LIFT   = [-0.2319, -0.5526,  1.3375,  0.7859,  1.5708,  0.0000]  # Cartesian Lift with Clearance (TCP Z = 0.48m, pointing down)
UR5_JIG_HOVER   = [-1.3791, -1.0623,  2.1130,  0.5201,  1.5708,  0.0000]  # Alignment Hover Above Jig (TCP Z = 0.565m, pointing down)
UR5_JIG_INSERT  = [-1.3791, -0.7571,  2.0886,  0.2393,  1.5708,  0.0000]  # Precision Seat into Jig (TCP Z = 0.445m, pointing down)
UR5_JIG_RETRACT = [-1.3791, -1.0623,  2.1130,  0.5201,  1.5708,  0.0000]  # Vertical Retract with Clearance (TCP Z = 0.565m, pointing down)

# OpenManipulator-X: [joint1 (yaw), joint2 (shoulder), joint3 (elbow), joint4 (wrist)]
# All poses strictly maintain joint2 + joint3 + joint4 = 0 so end-effector is parallel to ground and cylinder stays vertical
OM_STOWED       = [0.0, -0.55,    1.05,   -0.50]   # Tucked safely on TB3 deck, cylinder upright
OM_SHELF_HOVER  = [0.0,  0.45,   -0.70,    0.25]   # Pre-grasp hover approaching shelf part
OM_SHELF_GRASP  = [0.0,  0.6775, -0.8954,  0.2179] # Exact contact at (1.780, 1.20, 0.295)
OM_SHELF_LIFT   = [0.0,  0.45,   -0.70,    0.25]   # Vertical lift clearing shelf ledge
OM_DOCK_PRESENT = [0.0, -0.0905,  0.2374, -0.1469] # Smooth forward presentation onto dock receptacle (0.425, 0.0, 0.295)
OM_DOCK_RETRACT = [0.0, -0.55,    1.05,   -0.50]   # Safe smooth return to stowed configuration


class VisualWorkcellCoordinator(Node):
    def __init__(self):
        super().__init__('visual_workcell_coordinator')
        self.get_logger().info('Initializing Action-Driven Multi-Robot Visual Coordinator (with Pick & Place)...')

        self.declare_parameter('autonomous_demo', False)
        self.autonomous_demo = self.get_parameter('autonomous_demo').get_parameter_value().bool_value

        self.cb_group = ReentrantCallbackGroup()

        # Publishers
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.status_pub = self.create_publisher(String, '/workcell/coordination_status', 10)
        self.workpiece_pub = self.create_publisher(Marker, '/workcell/workpiece_marker', 10)
        self.text_marker_pub = self.create_publisher(Marker, '/workcell/status_text_marker', 10)

        # Mutex Lock Service Server
        self.lock_service = self.create_service(
            AcquireHandoffLock,
            'acquire_transfer_lock',
            self.handle_lock_request,
            callback_group=self.cb_group
        )
        self.locked_by = None
        self.zone_locked = False

        # Action Server: Navigate & Pick (Mobile Manipulator)
        self.tb3_action_server = ActionServer(
            self,
            NavigateAndPick,
            'navigate_and_pick',
            execute_callback=self.execute_tb3_action,
            goal_callback=self.goal_tb3_callback,
            cancel_callback=self.cancel_tb3_callback,
            callback_group=self.cb_group
        )

        # Action Server: UR5 Pick & Assemble (Fixed Manipulator)
        self.ur5_action_server = ActionServer(
            self,
            UR5PickAndPlace,
            'ur5_pick_and_assemble',
            execute_callback=self.execute_ur5_action,
            goal_callback=self.goal_ur5_callback,
            callback_group=self.cb_group
        )

        # Workcell Waypoints & Coordinates (Clearance from table front at X=0.30: dock_x=0.20 gives 3.1cm visible gap)
        self.shelf_x, self.shelf_y = 1.47, 1.20
        self.corridor_x = -0.05
        self.corner_x, self.corner_y = -0.05, 1.20
        self.dock_x, self.dock_y = 0.20, 0.00

        # Animated Joint Names (19 joints matching full URDF kinematic trees)
        self.joint_names = [
            'tb3_x_joint',
            'tb3_y_joint',
            'tb3_yaw_joint',
            'tb3_wheel_left_joint',
            'tb3_wheel_right_joint',
            'om_joint1',
            'om_joint2',
            'om_joint3',
            'om_joint4',
            'om_gripper_left_joint',
            'om_gripper_right_joint',
            'ur5_shoulder_pan_joint',
            'ur5_shoulder_lift_joint',
            'ur5_elbow_joint',
            'ur5_wrist_1_joint',
            'ur5_wrist_2_joint',
            'ur5_wrist_3_joint',
            'ur5_finger_left_joint',
            'ur5_finger_right_joint'
        ]

        # State Machine Variables
        self.system_state = 'IDLE'
        self.tb3_trajectory_time = 0.0
        self.ur5_trajectory_time = 0.0
        self.ret_trajectory_time = 0.0
        self.demo_timer = 0.0
        self.wheel_angle = 0.0
        self.last_phase_msg = ''
        self.workpiece_placed = False

        self.active_tb3_goal_handle = None
        self.active_ur5_goal_handle = None

        # 30 Hz Timer for kinematic interpolation & marker publishing
        self.timer = self.create_timer(1.0 / 30.0, self.update_simulation_state, callback_group=self.cb_group)

        self.get_logger().info('=' * 70)
        self.get_logger().info('★ Multi-Robot Visual Workcell ACTIVE with TRUE MECHANICAL ARTICULATION')
        self.get_logger().info('★ Dynamic Workpiece Marker: /workcell/workpiece_marker')
        self.get_logger().info('★ Action Servers: /navigate_and_pick & /ur5_pick_and_assemble')
        self.get_logger().info(f'★ Mode: {"AUTONOMOUS DEMO" if self.autonomous_demo else "ACTION-DRIVEN (Awaiting Goals)"}')
        self.get_logger().info('=' * 70)

    # -------------------------------------------------------------------------
    # Mutex Service Server Callback
    # -------------------------------------------------------------------------
    def handle_lock_request(self, request, response):
        robot = request.robot_id
        req_lock = request.request_lock
        zone = request.zone_id

        if req_lock:
            if self.locked_by is None:
                self.locked_by = robot
                self.zone_locked = True
                response.lock_granted = True
                response.message = f'Transfer zone {zone} lock GRANTED to {robot}.'
                self.get_logger().info(f'[MUTEX LOCKED] Zone {zone} acquired by: {robot}')
            elif self.locked_by == robot:
                response.lock_granted = True
                response.message = f'Zone {zone} lock already held by {robot}.'
            else:
                response.lock_granted = False
                response.message = f'Zone {zone} locked by {self.locked_by}. Access Denied.'
                self.get_logger().warn(f'[MUTEX CONTENTION] {robot} denied; zone locked by {self.locked_by}')
        else:
            if self.locked_by == robot or robot == 'multi_robot_coordinator':
                self.locked_by = None
                self.zone_locked = False
                response.lock_granted = True
                response.message = f'Zone {zone} lock released.'
                self.get_logger().info(f'[MUTEX RELEASED] Transfer zone {zone} is now available.')
            else:
                response.lock_granted = False
                response.message = f'Cannot release lock held by {self.locked_by}.'

        response.timestamp = int(time.time())
        return response

    # -------------------------------------------------------------------------
    # TB3 Navigate & Pick Action Callbacks
    # -------------------------------------------------------------------------
    def goal_tb3_callback(self, goal_request):
        self.get_logger().info(
            f'>>> TB3 Goal Received: Station="{goal_request.target_station_id}", Priority={goal_request.priority_level}'
        )
        return GoalResponse.ACCEPT

    def cancel_tb3_callback(self, goal_handle):
        self.get_logger().warn('Received request to cancel Mobile Robot Action Goal!')
        return CancelResponse.ACCEPT

    def execute_tb3_action(self, goal_handle):
        self.get_logger().info('[TB3 ACTION] Commencing Mobile Retrieval & Shelf Pick...')
        self.active_tb3_goal_handle = goal_handle
        self.tb3_trajectory_time = 0.0
        self.workpiece_placed = False
        self.system_state = 'TB3_ACTIVE'

        while self.system_state == 'TB3_ACTIVE':
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.system_state = 'IDLE'
                res = NavigateAndPick.Result()
                res.success = False
                res.status_message = 'Goal Canceled'
                return res
            time.sleep(0.033)

        goal_handle.succeed()
        res = NavigateAndPick.Result()
        res.success = True
        res.status_message = 'Workpiece retrieved from shelf and presented at transfer dock.'
        res.total_navigation_time = 11.5
        self.get_logger().info('>>> Mobile Robot Action Goal SUCCEEDED! Workpiece presented at Handoff Dock.')
        return res

    # -------------------------------------------------------------------------
    # UR5 Pick & Assemble Action Callbacks
    # -------------------------------------------------------------------------
    def goal_ur5_callback(self, goal_request):
        self.get_logger().info(f'>>> UR5 Goal Received: Task ID="{goal_request.task_id}"')
        return GoalResponse.ACCEPT

    def execute_ur5_action(self, goal_handle):
        self.get_logger().info('[UR5 ACTION] Commencing MoveIt 2 Pick, Transfer & Jig Assembly...')
        self.active_ur5_goal_handle = goal_handle
        self.ur5_trajectory_time = 0.0
        self.system_state = 'UR5_ACTIVE'

        while self.system_state == 'UR5_ACTIVE':
            time.sleep(0.033)

        goal_handle.succeed()
        res = UR5PickAndPlace.Result()
        res.success = True
        res.completion_code = 'ASSEMBLY_SUCCESSFUL_INSPECTION_PASSED'
        res.execution_time_seconds = 12.5
        self.get_logger().info('>>> UR5 Pick-and-Assemble SUCCEEDED! Part secured in Assembly Jig.')
        return res

    # -------------------------------------------------------------------------
    # Main 30 Hz Simulation State Machine & Kinematic Interpolation
    # -------------------------------------------------------------------------
    def update_simulation_state(self):
        dt = 1.0 / 30.0
        now = self.get_clock().now().to_msg()

        curr_x = self.shelf_x
        curr_y = self.shelf_y
        yaw = 0.0
        wheel_speed = 0.0

        # Default OpenManipulator Stowed Travel Pose
        om_q = list(OM_STOWED)
        om_grip = 0.002

        # Default UR5 Elevated Staging / Home Pose
        ur5_q = list(UR5_HOME)
        ur5_grip = 0.020

        current_phase_text = ''

        # ---------------------------------------------------------------------
        # STATE 0: IDLE
        # ---------------------------------------------------------------------
        if self.system_state == 'IDLE':
            curr_x = self.shelf_x
            curr_y = self.shelf_y
            yaw = 0.0
            wheel_speed = 0.0
            om_q = list(OM_STOWED)
            om_grip = 0.002
            ur5_q = list(UR5_HOME)
            ur5_grip = 0.020
            current_phase_text = '[IDLE] Workcell Ready. Awaiting Goal on /navigate_and_pick...'

            if self.autonomous_demo:
                self.demo_timer += dt
                if self.demo_timer > 2.5:
                    self.demo_timer = 0.0
                    self.system_state = 'TB3_ACTIVE'
                    self.tb3_trajectory_time = 0.0
                    self.workpiece_placed = False

        # ---------------------------------------------------------------------
        # STATE 1: TB3 EXECUTING PICK & TRANSIT (t: 0.0s to 11.5s)
        # ---------------------------------------------------------------------
        elif self.system_state == 'TB3_ACTIVE':
            self.tb3_trajectory_time += dt
            t = self.tb3_trajectory_time

            # 1A: Shelf Pick Operation (t: 0.0s to 4.0s)
            if t < 4.0:
                curr_x = self.shelf_x
                curr_y = self.shelf_y
                yaw = 0.0
                wheel_speed = 0.0

                if t < 1.2:
                    # Subphase 1.1: Unfold arm & Open gripper in pre-grasp hover
                    s = smooth_step(t / 1.2)
                    om_q = lerp(OM_STOWED, OM_SHELF_HOVER, s)
                    om_grip = 0.002 + (0.018 - 0.002) * s
                    current_phase_text = '[TB3 ACTION] Approaching Workpiece on Shelf Ledge'
                elif t < 2.0:
                    # Subphase 1.2: Reach down and enclose workpiece
                    s = smooth_step((t - 1.2) / 0.8)
                    om_q = lerp(OM_SHELF_HOVER, OM_SHELF_GRASP, s)
                    om_grip = 0.018
                    current_phase_text = '[TB3 ACTION] Gripper Enclosing Workpiece on Shelf'
                elif t < 2.6:
                    # Subphase 1.3: Gripper fingers clamp firmly around cylinder
                    s = smooth_step((t - 2.0) / 0.6)
                    om_q = list(OM_SHELF_GRASP)
                    om_grip = 0.018 + (0.002 - 0.018) * s
                    current_phase_text = '[TB3 ACTION] Workpiece FIRMLY CLAMPED!'
                elif t < 3.3:
                    # Subphase 1.4: Vertical lift-off from shelf ledge
                    s = smooth_step((t - 2.6) / 0.7)
                    om_q = lerp(OM_SHELF_GRASP, OM_SHELF_LIFT, s)
                    om_grip = 0.002
                    current_phase_text = '[TB3 ACTION] Lifting Workpiece with Shelf Clearance'
                else:
                    # Subphase 1.5: Tuck arm safely onto TB3 deck for travel
                    s = smooth_step((t - 3.3) / 0.7)
                    om_q = lerp(OM_SHELF_LIFT, OM_STOWED, s)
                    om_grip = 0.002
                    current_phase_text = '[TB3 ACTION] Arm Stowed Safely for Mobile Transit'

                if self.active_tb3_goal_handle:
                    fb = NavigateAndPick.Feedback()
                    fb.current_phase = 'OPENMANIPULATOR_GRASPING'
                    fb.percent_complete = float(min(35.0, (t / 4.0) * 35.0))
                    fb.current_pose_x = float(curr_x)
                    fb.current_pose_y = float(curr_y)
                    self.active_tb3_goal_handle.publish_feedback(fb)

            # 1B: Corridor Transit Navigation (t: 4.0s to 10.0s, duration 6.0s)
            elif t < 10.0:
                om_q = list(OM_STOWED)
                om_grip = 0.002
                nav_p = (t - 4.0) / 6.0
                current_phase_text = '[TB3 ACTION] Transporting Workpiece to Handoff Dock'

                if nav_p < 0.12:
                    sub_p = nav_p / 0.12
                    s = smooth_step(sub_p)
                    curr_x = self.shelf_x
                    curr_y = self.shelf_y
                    yaw = 0.0 + (math.pi - 0.0) * s
                    wheel_speed = 0.0
                elif nav_p < 0.45:
                    sub_p = (nav_p - 0.12) / 0.33
                    s = smooth_step(sub_p)
                    curr_x = self.shelf_x + (self.corridor_x - self.shelf_x) * s
                    curr_y = self.shelf_y
                    yaw = math.pi
                    wheel_speed = 9.0 * math.sin(sub_p * math.pi)
                elif nav_p < 0.58:
                    sub_p = (nav_p - 0.45) / 0.13
                    s = smooth_step(sub_p)
                    curr_x = self.corridor_x
                    curr_y = self.shelf_y
                    yaw = math.pi - (math.pi - (-math.pi / 2.0)) * s
                    wheel_speed = 0.0
                elif nav_p < 0.80:
                    sub_p = (nav_p - 0.58) / 0.22
                    s = smooth_step(sub_p)
                    curr_x = self.corridor_x
                    curr_y = self.shelf_y + (self.dock_y - self.shelf_y) * s
                    yaw = -math.pi / 2.0
                    wheel_speed = 9.0 * math.sin(sub_p * math.pi)
                elif nav_p < 0.90:
                    sub_p = (nav_p - 0.80) / 0.10
                    s = smooth_step(sub_p)
                    curr_x = self.corridor_x
                    curr_y = self.dock_y
                    yaw = -math.pi / 2.0 + (0.0 - (-math.pi / 2.0)) * s
                    wheel_speed = 0.0
                else:
                    sub_p = (nav_p - 0.90) / 0.10
                    s = smooth_step(sub_p)
                    curr_x = self.corridor_x + (self.dock_x - self.corridor_x) * s
                    curr_y = self.dock_y
                    yaw = 0.0
                    wheel_speed = 6.0 * math.sin(sub_p * math.pi)

                if self.active_tb3_goal_handle:
                    fb = NavigateAndPick.Feedback()
                    fb.current_phase = 'NAVIGATING_TO_HANDOFF'
                    fb.percent_complete = float(35.0 + nav_p * 45.0)
                    fb.current_pose_x = float(curr_x)
                    fb.current_pose_y = float(curr_y)
                    self.active_tb3_goal_handle.publish_feedback(fb)

            # 1C: Docking & Workpiece Presentation (t: 10.0s to 11.5s, duration 1.5s)
            elif t < 11.5:
                curr_x = self.dock_x
                curr_y = self.dock_y
                yaw = 0.0
                wheel_speed = 0.0
                dock_p = (t - 10.0) / 1.5
                s = smooth_step(dock_p)
                om_q = lerp(OM_STOWED, OM_DOCK_PRESENT, s)
                om_grip = 0.002
                current_phase_text = '[TB3 ACTION] Docked at Transfer Station - Presenting Workpiece'

                if self.active_tb3_goal_handle:
                    fb = NavigateAndPick.Feedback()
                    fb.current_phase = 'PRESENTING_PART_AT_DOCK'
                    fb.percent_complete = float(80.0 + dock_p * 20.0)
                    fb.current_pose_x = float(curr_x)
                    fb.current_pose_y = float(curr_y)
                    self.active_tb3_goal_handle.publish_feedback(fb)
            else:
                curr_x = self.dock_x
                curr_y = self.dock_y
                yaw = 0.0
                om_q = list(OM_DOCK_PRESENT)
                om_grip = 0.002
                self.system_state = 'TB3_DOCKED_WAITING_HANDOFF'
                current_phase_text = '[TB3 READY] Workpiece Ready at Receptacle. Awaiting UR5 Handshake.'

                if self.autonomous_demo:
                    self.system_state = 'UR5_ACTIVE'
                    self.ur5_trajectory_time = 0.0

        # ---------------------------------------------------------------------
        # STATE 2: TB3 DOCKED WAITING HANDOFF
        # ---------------------------------------------------------------------
        elif self.system_state == 'TB3_DOCKED_WAITING_HANDOFF':
            curr_x = self.dock_x
            curr_y = self.dock_y
            yaw = 0.0
            om_q = list(OM_DOCK_PRESENT)
            om_grip = 0.002
            ur5_q = list(UR5_HOME)
            ur5_grip = 0.020
            current_phase_text = '[TB3 DOCKED] Holding Workpiece over Yellow Dock Pad. Ready for Handshake.'

        # ---------------------------------------------------------------------
        # STATE 3: UR5 EXECUTING ASSEMBLY (t: 0.0s to 12.5s)
        # ---------------------------------------------------------------------
        elif self.system_state == 'UR5_ACTIVE':
            self.ur5_trajectory_time += dt
            t = self.ur5_trajectory_time
            curr_x = self.dock_x
            curr_y = self.dock_y
            yaw = 0.0

            # 3A: Approach Dock (t: 0.0s to 2.0s) -> Hover over yellow dock pad
            if t < 2.0:
                om_q = list(OM_DOCK_PRESENT)
                om_grip = 0.002
                s = smooth_step(t / 2.0)
                ur5_q = lerp(UR5_HOME, UR5_DOCK_HOVER, s)
                ur5_grip = 0.020
                current_phase_text = '[UR5 ACTION] Approaching Handoff Dock (Pre-Grasp Hover)'

                if self.active_ur5_goal_handle:
                    fb = UR5PickAndPlace.Feedback()
                    fb.joint_trajectory_state = 'MOVEIT_APPROACHING_HANDOFF'
                    fb.progress_fraction = 0.15
                    self.active_ur5_goal_handle.publish_feedback(fb)

            # 3B: Vertical Descent to Workpiece (t: 2.0s to 3.5s)
            elif t < 3.5:
                om_q = list(OM_DOCK_PRESENT)
                om_grip = 0.002
                s = smooth_step((t - 2.0) / 1.5)
                ur5_q = lerp(UR5_DOCK_HOVER, UR5_DOCK_GRASP, s)
                ur5_grip = 0.020
                current_phase_text = '[UR5 ACTION] Descending Vertically to Enclose Workpiece'

                if self.active_ur5_goal_handle:
                    fb = UR5PickAndPlace.Feedback()
                    fb.joint_trajectory_state = 'VERTICAL_DESCENT_TO_DOCK'
                    fb.progress_fraction = 0.30
                    self.active_ur5_goal_handle.publish_feedback(fb)

            # 3C: Synchronized Handshake Transfer (t: 3.5s to 4.8s)
            elif t < 4.8:
                s = smooth_step((t - 3.5) / 1.3)
                ur5_q = list(UR5_DOCK_GRASP)
                ur5_grip = 0.020 + (0.007 - 0.020) * s
                om_grip = 0.002 + (0.018 - 0.002) * s
                om_q = list(OM_DOCK_PRESENT)  # TB3 holds perfectly steady while grippers transfer
                current_phase_text = '[HANDSHAKE] Transferring Workpiece: UR5 Clamping & TB3 Releasing'

                if self.active_ur5_goal_handle:
                    fb = UR5PickAndPlace.Feedback()
                    fb.joint_trajectory_state = 'CLOSING_GRIPPER'
                    fb.progress_fraction = 0.45
                    self.active_ur5_goal_handle.publish_feedback(fb)

            # 3D: Safe Separation: UR5 Vertical Lift & TB3 Safe Stow (t: 4.8s to 6.5s)
            elif t < 6.5:
                s = smooth_step((t - 4.8) / 1.7)
                ur5_q = lerp(UR5_DOCK_GRASP, UR5_DOCK_LIFT, s)
                ur5_grip = 0.007
                om_q = lerp(OM_DOCK_PRESENT, OM_STOWED, s)
                om_grip = 0.018 + (0.002 - 0.018) * s  # TB3 closes gripper once arm safely stows
                current_phase_text = '[UR5 ACTION] Vertical Lift with Clearance | TB3 Stowing Arm'

                if self.active_ur5_goal_handle:
                    fb = UR5PickAndPlace.Feedback()
                    fb.joint_trajectory_state = 'CARTESIAN_LIFT_CLEARANCE'
                    fb.progress_fraction = 0.60
                    self.active_ur5_goal_handle.publish_feedback(fb)

            # 3E: Direct Smooth Arc Swing Across Table to Jig (t: 6.5s to 9.0s)
            elif t < 9.0:
                om_q = list(OM_STOWED)
                om_grip = 0.002
                s = smooth_step((t - 6.5) / 2.5)
                ur5_q = lerp(UR5_DOCK_LIFT, UR5_JIG_HOVER, s)
                ur5_grip = 0.007
                current_phase_text = '[UR5 ACTION] Carrying Workpiece across Table to Assembly Jig'

                if self.active_ur5_goal_handle:
                    fb = UR5PickAndPlace.Feedback()
                    fb.joint_trajectory_state = 'TRANSIT_TO_ASSEMBLY_FIXTURE'
                    fb.progress_fraction = 0.75
                    self.active_ur5_goal_handle.publish_feedback(fb)

            # 3F: Precision Insertion into Jig Clamp (t: 9.0s to 10.3s)
            elif t < 10.3:
                om_q = list(OM_STOWED)
                om_grip = 0.002
                s = smooth_step((t - 9.0) / 1.3)
                ur5_q = lerp(UR5_JIG_HOVER, UR5_JIG_INSERT, s)
                ur5_grip = 0.007
                current_phase_text = '[UR5 ACTION] Precision Assembly: Seating Workpiece in Jig Clamp'

                if self.active_ur5_goal_handle:
                    fb = UR5PickAndPlace.Feedback()
                    fb.joint_trajectory_state = 'PRECISION_ASSEMBLY_INSERTION'
                    fb.progress_fraction = 0.90
                    self.active_ur5_goal_handle.publish_feedback(fb)

            # 3G: Part Release & Vertical Retraction (t: 10.3s to 11.4s)
            elif t < 11.4:
                self.workpiece_placed = True
                om_q = list(OM_STOWED)
                om_grip = 0.002
                s = smooth_step((t - 10.3) / 1.1)
                ur5_q = lerp(UR5_JIG_INSERT, UR5_JIG_RETRACT, s)
                ur5_grip = 0.007 + (0.020 - 0.007) * s
                current_phase_text = '[UR5 ACTION] Assembly Complete! Part Seated in Jig Fixture'

                if self.active_ur5_goal_handle:
                    fb = UR5PickAndPlace.Feedback()
                    fb.joint_trajectory_state = 'ASSEMBLY_RELEASE_AND_RETRACT'
                    fb.progress_fraction = 0.98
                    self.active_ur5_goal_handle.publish_feedback(fb)

            # 3H: Return to Home Staging Pose (t: 11.4s to 12.5s)
            elif t < 12.5:
                self.workpiece_placed = True
                om_q = list(OM_STOWED)
                om_grip = 0.002
                s = smooth_step((t - 11.4) / 1.1)
                ur5_q = lerp(UR5_JIG_RETRACT, UR5_HOME, s)
                ur5_grip = 0.020
                current_phase_text = '[UR5 ACTION] Retracting Arm to Elevated Staging Pose'

                if self.active_ur5_goal_handle:
                    fb = UR5PickAndPlace.Feedback()
                    fb.joint_trajectory_state = 'RETURN_TO_HOME_POSE'
                    fb.progress_fraction = 1.00
                    self.active_ur5_goal_handle.publish_feedback(fb)
            else:
                self.workpiece_placed = True
                om_q = list(OM_STOWED)
                om_grip = 0.002
                ur5_q = list(UR5_HOME)
                ur5_grip = 0.020
                self.system_state = 'TB3_RETURNING'
                self.ret_trajectory_time = 0.0
                current_phase_text = '[ASSEMBLY COMPLETE] Part Assembled into Jig! TB3 Returning'

        # ---------------------------------------------------------------------
        # STATE 4: TB3 RETURNING TO SHELF DOCK (t: 0.0s to 5.5s)
        # ---------------------------------------------------------------------
        elif self.system_state == 'TB3_RETURNING':
            self.ret_trajectory_time += dt
            t = self.ret_trajectory_time
            ret_p = t / 5.5
            om_q = list(OM_STOWED)
            om_grip = 0.002
            ur5_q = list(UR5_HOME)
            ur5_grip = 0.020
            current_phase_text = '[TB3 RETURN] Driving Corridor back to Storage Shelf'

            if ret_p < 0.15:
                # 1. Reverse straight back into wide open aisle (yaw = 0.0)
                sub_p = ret_p / 0.15
                s = smooth_step(sub_p)
                curr_x = self.dock_x + (self.corridor_x - self.dock_x) * s
                curr_y = self.dock_y
                yaw = 0.0
                wheel_speed = -6.0 * math.sin(sub_p * math.pi)
            elif ret_p < 0.28:
                # 2. Rotate in open aisle to face north (yaw = pi/2)
                sub_p = (ret_p - 0.15) / 0.13
                s = smooth_step(sub_p)
                curr_x = self.corridor_x
                curr_y = self.dock_y
                yaw = 0.0 + (math.pi / 2.0) * s
                wheel_speed = 0.0
            elif ret_p < 0.60:
                # 3. Drive north down wide open corridor (clearance > 20 cm from table)
                sub_p = (ret_p - 0.28) / 0.32
                s = smooth_step(sub_p)
                curr_x = self.corridor_x
                curr_y = self.dock_y + (self.shelf_y - self.dock_y) * s
                yaw = math.pi / 2.0
                wheel_speed = 9.0 * math.sin(sub_p * math.pi)
            elif ret_p < 0.72:
                # 4. Rotate to face east towards shelf
                sub_p = (ret_p - 0.60) / 0.12
                s = smooth_step(sub_p)
                curr_x = self.corridor_x
                curr_y = self.shelf_y
                yaw = math.pi / 2.0 - (math.pi / 2.0) * s
                wheel_speed = 0.0
            elif ret_p < 0.95:
                # 5. Drive east into shelf dock
                sub_p = (ret_p - 0.72) / 0.23
                s = smooth_step(sub_p)
                curr_x = self.corridor_x + (self.shelf_x - self.corridor_x) * s
                curr_y = self.shelf_y
                yaw = 0.0
                wheel_speed = 9.0 * math.sin(sub_p * math.pi)
            elif ret_p < 1.0:
                curr_x = self.shelf_x
                curr_y = self.shelf_y
                yaw = 0.0
                wheel_speed = 0.0
            else:
                self.system_state = 'IDLE'
                self.demo_timer = 0.0
                current_phase_text = '[IDLE] Cycle Complete. Awaiting next Task on /navigate_and_pick...'

        self.wheel_angle += wheel_speed * dt

        # Publish JointState (19 joints matching URDF)
        js = JointState()
        js.header.stamp = now
        js.name = self.joint_names
        js.position = [
            float(curr_x),
            float(curr_y),
            float(yaw),
            float(self.wheel_angle),
            float(self.wheel_angle),
            float(om_q[0]),
            float(om_q[1]),
            float(om_q[2]),
            float(om_q[3]),
            float(om_grip),
            float(om_grip),
            float(ur5_q[0]),
            float(ur5_q[1]),
            float(ur5_q[2]),
            float(ur5_q[3]),
            float(ur5_q[4]),
            float(ur5_q[5]),
            float(ur5_grip),
            float(ur5_grip)
        ]
        self.joint_pub.publish(js)

        # Publish Dynamic Workpiece Marker (Visible Physical Pick & Place!)
        self.publish_dynamic_workpiece(now, current_phase_text)

        # Status Topic
        if current_phase_text != self.last_phase_msg:
            self.last_phase_msg = current_phase_text
            self.get_logger().info(current_phase_text)
            msg = String()
            msg.data = current_phase_text
            self.status_pub.publish(msg)

    def publish_dynamic_workpiece(self, now, phase_text):
        m = Marker()
        m.header.stamp = now
        m.ns = 'workpiece'
        m.id = 100
        m.type = Marker.CYLINDER
        m.action = Marker.ADD
        m.scale.x = 0.032
        m.scale.y = 0.032
        m.scale.z = 0.055
        # Vibrant Gold metallic color
        m.color.r = 0.98
        m.color.g = 0.78
        m.color.b = 0.12
        m.color.a = 1.0

        # Dynamic TF Attachment Logic
        if self.system_state == 'IDLE' and not self.workpiece_placed:
            # 1. Sitting on lower shelf pick ledge
            m.header.frame_id = 'world'
            m.pose.position.x = 1.78
            m.pose.position.y = 1.20
            m.pose.position.z = 0.295
            m.pose.orientation.w = 1.0
        elif self.system_state == 'TB3_ACTIVE':
            if self.tb3_trajectory_time < 2.3:
                # Approaching shelf: still on ledge
                m.header.frame_id = 'world'
                m.pose.position.x = 1.78
                m.pose.position.y = 1.20
                m.pose.position.z = 0.295
                m.pose.orientation.w = 1.0
            else:
                # Grasp acquired! Follows OpenManipulator gripper across shop floor!
                m.header.frame_id = 'om_link5'
                m.pose.position.x = 0.10
                m.pose.position.y = 0.0
                m.pose.position.z = 0.0
                m.pose.orientation.w = 1.0
        elif self.system_state == 'TB3_DOCKED_WAITING_HANDOFF':
            # Presented forward in OpenManipulator gripper over yellow dock pad
            m.header.frame_id = 'om_link5'
            m.pose.position.x = 0.10
            m.pose.position.y = 0.0
            m.pose.position.z = 0.0
            m.pose.orientation.w = 1.0
        elif self.system_state == 'UR5_ACTIVE':
            if self.ur5_trajectory_time < 4.2:
                # UR5 reaching down and clamping: still held by OM-X
                m.header.frame_id = 'om_link5'
                m.pose.position.x = 0.10
                m.pose.position.y = 0.0
                m.pose.position.z = 0.0
                m.pose.orientation.w = 1.0
            elif self.ur5_trajectory_time < 10.3:
                # Handover complete! Clamped in UR5 gripper, swinging to jig!
                m.header.frame_id = 'ur5_gripper_base'
                m.pose.position.x = 0.0
                m.pose.position.y = 0.0
                m.pose.position.z = 0.075
                m.pose.orientation.w = 1.0
            else:
                # Inserted & Seated in Assembly Jig!
                self.workpiece_placed = True
                m.header.frame_id = 'assembly_jig'
                m.pose.position.x = 0.0
                m.pose.position.y = 0.0
                m.pose.position.z = 0.045
                m.pose.orientation.w = 1.0
        else:
            # Assembly Jig has the part
            m.header.frame_id = 'assembly_jig'
            m.pose.position.x = 0.0
            m.pose.position.y = 0.0
            m.pose.position.z = 0.045
            m.pose.orientation.w = 1.0

        self.workpiece_pub.publish(m)

        # Floating 3D Text Badge above workcell
        tm = Marker()
        tm.header.stamp = now
        tm.header.frame_id = 'world'
        tm.ns = 'status_badge'
        tm.id = 101
        tm.type = Marker.TEXT_VIEW_FACING
        tm.action = Marker.ADD
        tm.pose.position.x = 0.85
        tm.pose.position.y = 0.35
        tm.pose.position.z = 1.25
        tm.scale.z = 0.040
        tm.color.r = 0.20
        tm.color.g = 0.90
        tm.color.b = 1.00
        tm.color.a = 1.0
        tm.text = phase_text
        self.text_marker_pub.publish(tm)


def main(args=None):
    rclpy.init(args=args)
    node = VisualWorkcellCoordinator()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except BaseException:
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception:
                pass


if __name__ == '__main__':
    main()
