"""
Task Scheduler Engine for Multi-Robot Coordination in ROS 2.
Implements:
1. FIFO (First-In, First-Out)
2. Priority-Based Scheduling (Min-Heap based on priority weight)
3. Round-Robin Scheduling (Fair time/task quantum allocation)
"""
import heapq
from collections import deque

class Task:
    def __init__(self, task_id, priority, tb3_duration, ur5_duration, arrival_time=0.0):
        self.task_id = task_id
        self.priority = priority  # 1 = Urgent/High, 2 = Medium, 3 = Normal, 4 = Low
        self.tb3_duration = tb3_duration  # Time taken for TB3 navigation + pick
        self.ur5_duration = ur5_duration  # Time taken for UR5 transfer + assembly
        self.arrival_time = arrival_time
        self.start_time = None
        self.handoff_time = None
        self.completion_time = None
        self.waiting_time = 0.0

    def __lt__(self, other):
        # Priority queue comparison: lower numeric priority value means higher urgency
        if self.priority == other.priority:
            return self.arrival_time < other.arrival_time
        return self.priority < other.priority

class TaskScheduler:
    def __init__(self, mode='PRIORITY'):
        self.mode = mode.upper()
        self.fifo_queue = deque()
        self.priority_queue = []
        self.rr_queue = deque()
        self.completed_tasks = []

    def add_task(self, task):
        if self.mode == 'FIFO':
            self.fifo_queue.append(task)
        elif self.mode == 'PRIORITY':
            heapq.heappush(self.priority_queue, task)
        elif self.mode == 'ROUND_ROBIN':
            self.rr_queue.append(task)

    def get_next_task(self):
        if self.mode == 'FIFO':
            return self.fifo_queue.popleft() if self.fifo_queue else None
        elif self.mode == 'PRIORITY':
            return heapq.heappop(self.priority_queue) if self.priority_queue else None
        elif self.mode == 'ROUND_ROBIN':
            return self.rr_queue.popleft() if self.rr_queue else None
        return None

    def has_pending_tasks(self):
        if self.mode == 'FIFO':
            return len(self.fifo_queue) > 0
        elif self.mode == 'PRIORITY':
            return len(self.priority_queue) > 0
        elif self.mode == 'ROUND_ROBIN':
            return len(self.rr_queue) > 0
        return False
