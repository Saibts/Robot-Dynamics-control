"""
Launch file to start all nodes for Multi-Robot Coordination System:
1. Mutual Exclusion Lock Service Server
2. TurtleBot3 Action Server
3. UR5 Action Server
4. Multi-Robot Coordinator Node
"""
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='multi_robot_coordination',
            executable='lock_server',
            name='handoff_lock_server',
            output='screen'
        ),
        Node(
            package='multi_robot_coordination',
            executable='tb3_server',
            name='tb3_action_server',
            output='screen'
        ),
        Node(
            package='multi_robot_coordination',
            executable='ur5_server',
            name='ur5_action_server',
            output='screen'
        ),
        Node(
            package='multi_robot_coordination',
            executable='coordinator',
            name='multi_robot_coordinator',
            parameters=[{'scheduler_mode': 'PRIORITY'}],
            output='screen'
        ),
    ])
