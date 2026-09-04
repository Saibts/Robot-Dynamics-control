#!/usr/bin/env python3
"""
Interactive Demo Task Dispatcher & Live Progress Monitor.
Enqueues 3 demonstration tasks with staggered priorities:
  - Task 1: TASK_A_NORMAL (Priority 3, Station A)
  - Task 2: TASK_B_URGENT (Priority 1, Station B) -> Priority Overtake!
  - Task 3: TASK_C_HIGH   (Priority 2, Station A)

Then keeps the terminal open with a live visual progress bar so you can watch
the scheduling order and execution in real time!
"""

import time
import sys
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TaskDispatcherMonitor(Node):
    def __init__(self):
        super().__init__('demo_task_dispatcher')
        self.pub = self.create_publisher(String, '/submit_task', 10)
        self.sub = self.create_subscription(String, '/workcell/coordination_status', self.status_callback, 10)
        self.current_status = ''
        self.completed_cycles = 0

    def status_callback(self, msg):
        if msg.data != self.current_status:
            self.current_status = msg.data
            timestamp = time.strftime('%H:%M:%S')
            print(f'[{timestamp}] >> {msg.data}')
            if 'Cycle Complete' in msg.data or 'Part Assembled' in msg.data:
                self.completed_cycles += 1
                print(f'   ✔ Task Cycle #{self.completed_cycles} completed!')
                if self.completed_cycles >= 3:
                    print('=' * 68)
                    print('🎉 ALL 3 DEMONSTRATION TASKS SUCCESSFULLY EXECUTED!')
                    print('=' * 68)
                    sys.exit(0)


def main(args=None):
    rclpy.init(args=args)
    node = TaskDispatcherMonitor()

    print('=' * 68)
    print('★ MULTI-ROBOT TASK SCHEDULER: BATCH DISPATCHER & LIVE MONITOR ★')
    print('=' * 68)
    print('Waiting for Multi-Robot Coordinator to connect...')

    # Wait for coordinator subscriber
    for _ in range(30):
        if node.pub.get_subscription_count() > 0:
            break
        rclpy.spin_once(node, timeout_sec=0.2)
        time.sleep(0.1)

    tasks = [
        ('TASK_A_NORMAL', 3, 'STORAGE_STATION_A'),
        ('TASK_B_URGENT', 1, 'STORAGE_STATION_B'),
        ('TASK_C_HIGH', 2, 'STORAGE_STATION_A')
    ]

    print('')
    print('Enqueuing 3 Tasks to Coordinator:')
    for task_id, prio, station in tasks:
        msg = String()
        msg.data = f'{task_id},{prio},{station}'
        node.pub.publish(msg)
        print(f'  [+] Dispatched: {task_id:<16} | Priority: {prio} | Station: {station}')
        time.sleep(0.3)

    print('')
    print('=' * 68)
    print('Monitoring live execution in RViz2... (Press Ctrl+C to exit anytime)')
    print('=' * 68)

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
