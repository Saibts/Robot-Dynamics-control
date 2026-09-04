cmake_minimum_required(VERSION 3.8)
project(multi_robot_gazebo_sim)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# Install directories
install(DIRECTORY urdf worlds rviz launch meshes
  DESTINATION share/${PROJECT_NAME}
)

# Install executable scripts
install(PROGRAMS
  scripts/visual_workcell_coordinator.py
  scripts/coordinator.py
  scripts/scheduler.py
  scripts/submit_demo_tasks.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
