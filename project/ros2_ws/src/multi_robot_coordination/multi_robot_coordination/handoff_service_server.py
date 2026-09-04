"""
Service Server for Shared Transfer Zone Mutual Exclusion Lock.
Guarantees atomic handshake and collision prevention between Mobile Manipulator and Fixed UR5 Manipulator.
"""
import time
import rclpy
from rclpy.node import Node

try:
    from multi_robot_interfaces.srv import AcquireHandoffLock
except ImportError:
    from multi_robot_coordination.srv import AcquireHandoffLock

class HandoffLockServer(Node):
    def __init__(self):
        super().__init__('handoff_lock_server')
        self.srv = self.create_service(
            AcquireHandoffLock,
            'acquire_transfer_lock',
            self.handle_lock_request
        )
        self.locked_by = None
        self.get_logger().info('Shared Transfer Zone Lock Service Server Active.')

    def handle_lock_request(self, request, response):
        robot = request.robot_id
        req_lock = request.request_lock
        zone = request.zone_id

        if req_lock:
            if self.locked_by is None:
                self.locked_by = robot
                response.lock_granted = True
                response.message = f'Zone {zone} lock granted to {robot}.'
                self.get_logger().info(f'[MUTEX LOCKED] Granted to: {robot}')
            elif self.locked_by == robot:
                response.lock_granted = True
                response.message = f'Zone {zone} lock already held by {robot}.'
            else:
                response.lock_granted = False
                response.message = f'Zone {zone} currently locked by {self.locked_by}. Access Denied.'
                self.get_logger().warn(f'[MUTEX CONTENTION] {robot} denied; locked by {self.locked_by}')
        else:
            if self.locked_by == robot or self.locked_by == 'multi_robot_coordinator':
                self.locked_by = None
                response.lock_granted = True
                response.message = f'Zone {zone} lock released.'
                self.get_logger().info(f'[MUTEX RELEASED] Zone {zone} is now available.')
            else:
                response.lock_granted = False
                response.message = f'Cannot release lock held by {self.locked_by}.'

        response.timestamp = int(time.time())
        return response

def main(args=None):
    rclpy.init(args=args)
    node = HandoffLockServer()
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
