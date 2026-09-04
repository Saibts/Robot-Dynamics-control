# Folder 2: Gazebo and RViz 3D Workcell Simulation

This folder contains the action-driven 3D physical simulation and visual workcell in **RViz2 & Gazebo Harmonic** for ROS 2 Jazzy.

## Features

- **TurtleBot3 Waffle Pi + OpenManipulator-X**: 4-DOF mobile manipulator with strict pitch-constrained forward kinematics ($q_2 + q_3 + q_4 = 0$).
- **Universal Robots UR5**: 6-DOF industrial robot arm with custom parallel-jaw gripper.
- **Dynamic Workpiece**: Gold cylinder dynamically parented across coordinate frames (`world` -> `om_link5` -> `ur5_gripper_base` -> `assembly_jig`) with sub-millimeter precision ($< 0.02\text{ mm}$ handoff alignment).
- **Collision-Free Clearance**: TurtleBot3 docks at $X=0.20\text{ m}$ leaving a $3.1\text{ cm}$ clearance from the table edge ($X=0.30\text{ m}$).
- **Floating 3D Status Badge**: Real-time phase notification overlay hovering at $Z=1.25\text{ m}$.

## How to Build & Run

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash

# Continuous Autonomous Simulation Demo:
ros2 launch multi_robot_gazebo_sim workcell_simulation.launch.py autonomous_demo:=true

# Or Action-Driven Mode (controlled by Coordinator in Folder 1):
ros2 launch multi_robot_gazebo_sim workcell_simulation.launch.py
```
