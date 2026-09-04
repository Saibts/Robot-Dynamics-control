# Folder 1: Coordination and Task Scheduling

This folder contains the core academic codebase for **Task 3: Multi-Robot Coordination Using ROS 2 Actions and Services (Task Scheduling)**.

## Architecture

- **`multi_robot_interfaces`**: Defines custom ROS 2 Actions (`NavigateAndPick.action`, `UR5PickAndPlace.action`) and Services (`AcquireHandoffLock.srv`).
- **`multi_robot_coordination`**:
  - `multi_robot_coordinator.py`: Central coordination node implementing FIFO, Priority, and Round-Robin queue dispatching.
  - `tb3_action_server.py`: Simulates mobile manipulator navigation and pick action with real-time feedback.
  - `ur5_action_server.py`: Simulates 6-DOF industrial arm pick-and-place action.
  - `lock_server.py`: Mutex service protecting shared workspace collision zones.
  - `simulation_runner.py`: Benchmark runner comparing scheduling policies.
  - `submit_demo_tasks.py`: Task submission utility.

## Documentation Files

- `Complete_Multi_Robot_Coordination_ROS2_Massive_Project_Manual.pdf`
- `Complete_Multi_Robot_Coordination_ROS2_Master_Guide_Report.pdf`
- `Multi_Robot_Coordination_Component_Analysis_Chart.pdf`
- `ROS2_Jazzy_Step_By_Step_Execution_Guide.pdf`

## How to Build & Run

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 run multi_robot_coordination coordinator --ros-args -p scheduler_mode:=PRIORITY
```
