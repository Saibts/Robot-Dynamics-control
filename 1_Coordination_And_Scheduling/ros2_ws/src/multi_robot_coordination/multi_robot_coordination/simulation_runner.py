"""
Benchmark Simulation Runner for Multi-Robot Coordination.
Simulates heterogeneous task execution between:
1. TurtleBot3 + OpenManipulator (Mobile Manipulator)
2. UR5 (Fixed 6-DOF Industrial Manipulator)

Evaluates:
- Average Task Waiting Time (s)
- UR5 and TB3 Resource Utilization (%)
- System Throughput (Tasks/Hour)
- Total Makespan (s)
"""
import random
from scheduler import Task, TaskScheduler

def generate_benchmark_tasks(count=30, seed=101):
    random.seed(seed)
    tasks = []
    for i in range(1, count + 1):
        prio = random.choice([1, 2, 3, 4, 5])
        # TB3 navigation & pick duration: 12 - 24 seconds
        tb3_d = round(random.uniform(12.0, 22.0), 2)
        # UR5 pick & assemble duration: 9 - 17 seconds
        ur5_d = round(random.uniform(9.0, 16.0), 2)
        # Staggered task arrival times
        arrival = round(i * random.uniform(4.0, 7.5), 2)
        tasks.append(Task(f'TASK_{i:02d}', prio, tb3_d, ur5_d, arrival))
    return tasks

def simulate_pipeline(scheduler_mode, task_list):
    scheduler = TaskScheduler(mode=scheduler_mode)
    all_tasks = sorted(task_list, key=lambda t: t.arrival_time)
    
    current_time = 0.0
    task_idx = 0
    tb3_busy_until = 0.0
    ur5_busy_until = 0.0
    
    tb3_busy_time = 0.0
    ur5_busy_time = 0.0
    
    completed = []
    handoff_ready = []
    
    while task_idx < len(all_tasks) or scheduler.has_pending_tasks() or handoff_ready or tb3_busy_until > current_time or ur5_busy_until > current_time:
        # Ingest arriving tasks
        while task_idx < len(all_tasks) and all_tasks[task_idx].arrival_time <= current_time:
            scheduler.add_task(all_tasks[task_idx])
            task_idx += 1
            
        # Dispatch TB3 if idle
        if tb3_busy_until <= current_time and scheduler.has_pending_tasks():
            curr_task = scheduler.get_next_task()
            curr_task.start_time = current_time
            curr_task.waiting_time = max(0.0, current_time - curr_task.arrival_time)
            
            tb3_busy_until = current_time + curr_task.tb3_duration
            tb3_busy_time += curr_task.tb3_duration
            
            handoff_ready.append((tb3_busy_until, curr_task))
            
        # Dispatch UR5 if ready
        if ur5_busy_until <= current_time and handoff_ready:
            ready_candidates = [item for item in handoff_ready if item[0] <= current_time]
            if ready_candidates:
                ready_time, task_to_ur5 = ready_candidates[0]
                handoff_ready.remove((ready_time, task_to_ur5))
                
                ur5_busy_until = current_time + task_to_ur5.ur5_duration
                ur5_busy_time += task_to_ur5.ur5_duration
                task_to_ur5.completion_time = ur5_busy_until
                completed.append(task_to_ur5)
                
        # Advance time to next discrete event
        next_events = [tb3_busy_until, ur5_busy_until]
        if task_idx < len(all_tasks):
            next_events.append(all_tasks[task_idx].arrival_time)
        if handoff_ready:
            next_events.extend([item[0] for item in handoff_ready if item[0] > current_time])
            
        future_events = [e for e in next_events if e > current_time]
        if future_events:
            current_time = min(future_events)
        else:
            current_time += 1.0
            
    total_time = max(current_time, 1.0)
    avg_wait = sum(t.waiting_time for t in completed) / len(completed) if completed else 0.0
    ur5_util = (ur5_busy_time / total_time) * 100.0
    tb3_util = (tb3_busy_time / total_time) * 100.0
    throughput = (len(completed) / total_time) * 3600.0
    
    return {
        'mode': scheduler_mode,
        'completed_count': len(completed),
        'makespan_s': total_time,
        'avg_wait_s': avg_wait,
        'ur5_util_pct': ur5_util,
        'tb3_util_pct': tb3_util,
        'throughput_per_hr': throughput
    }

if __name__ == '__main__':
    raw_tasks = generate_benchmark_tasks(count=30, seed=101)
    results = {}
    for mode in ['FIFO', 'PRIORITY', 'ROUND_ROBIN']:
        tasks_copy = [Task(t.task_id, t.priority, t.tb3_duration, t.ur5_duration, t.arrival_time) for t in raw_tasks]
        res = simulate_pipeline(mode, tasks_copy)
        results[mode] = res
        print(f"=== {mode} Benchmark Results ===")
        for k, v in res.items():
            print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")
