import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('multi_robot_gazebo_sim')

    urdf_file = os.path.join(pkg_dir, 'urdf', 'multi_robot_workcell.urdf.xacro')
    rviz_config = os.path.join(pkg_dir, 'rviz', 'workcell_view.rviz')
    world_file = os.path.join(pkg_dir, 'worlds', 'workcell.sdf')

    with open(urdf_file, 'r') as infp:
        robot_description_content = infp.read()

    use_gazebo_arg = DeclareLaunchArgument(
        'use_gazebo',
        default_value='false',
        description='Whether to launch 3D Gazebo physics engine alongside RViz2'
    )

    autonomous_demo_arg = DeclareLaunchArgument(
        'autonomous_demo',
        default_value='false',
        description='Whether to run continuous autonomous demo (true) or await ROS 2 Action goals (false)'
    )

    # 1. Robot State Publisher (Broadcasts full 3D workcell model to /robot_description & static/dynamic TF)
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='workcell_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': False
        }]
    )

    # 2. Action-Driven Visual Workcell Coordinator
    visual_coordinator_node = Node(
        package='multi_robot_gazebo_sim',
        executable='visual_workcell_coordinator.py',
        name='visual_workcell_coordinator',
        parameters=[{
            'autonomous_demo': LaunchConfiguration('autonomous_demo')
        }],
        output='screen'
    )

    # 3. RViz2 3D Visualizer (Pre-configured camera view and material render settings)
    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen'
    )

    # 4. Optional Gazebo Harmonic Process
    gazebo_process = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_file],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_gazebo'))
    )

    # 5. Spawn model in Gazebo Harmonic
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'multi_robot_workcell', '-allow_renaming', 'true'],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_gazebo'))
    )

    nodes_to_start = [
        use_gazebo_arg,
        autonomous_demo_arg,
        robot_state_publisher_node,
        visual_coordinator_node,
        rviz2_node,
        gazebo_process,
        gz_spawn_entity,
    ]

    return LaunchDescription(nodes_to_start)
