"""
Multi-Robot Coordination Package.
Bridges multi_robot_interfaces action & srv definitions into multi_robot_coordination namespace.
"""
import sys
try:
    import multi_robot_interfaces.action as action
    import multi_robot_interfaces.srv as srv
    sys.modules['multi_robot_coordination.action'] = action
    sys.modules['multi_robot_coordination.srv'] = srv
except ImportError:
    pass
