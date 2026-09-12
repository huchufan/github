from datetime import datetime, timedelta
from agent.orchestration.core.monitor import ExecutionMonitor, AdaptiveReplanner
from agent.core.types import ExecutionState, ExecutionPlan, SubTask, TaskResult, ExecutionMetrics


def make_plan_var(levels):
    subtasks = []
    execution_order = []
    idx = 1
    for cnt in levels:
        level = []
        for _ in range(cnt):
            t = SubTask(id=f't{idx}', skill_name='s')
            subtasks.append(t)
            level.append(t)
            idx += 1
        execution_order.append(level)
    return ExecutionPlan(subtasks=subtasks, execution_order=execution_order, time_estimate=10)


def test_calc_avg_and_empty():
    mon = ExecutionMonitor()
    # empty durations
    assert mon.calculate_avg_duration([]) == 0.0
    # avg with values
    tr1 = TaskResult(task_id='t1', status='SUCCESS', result={}, duration=2.0, success=True)
    tr2 = TaskResult(task_id='t2', status='SUCCESS', result={}, duration=4.0, success=True)
    assert mon.calculate_avg_duration([tr1, tr2]) == 3.0


def test_parallelism_efficiency_and_critical_path():
    mon = ExecutionMonitor()
    plan = make_plan_var([3, 2])
    state = ExecutionState(plan=plan, start_time=datetime.now())
    # no completed
    state.tasks_completed = []
    assert mon.calculate_parallelism_efficiency(state) == 0.0
    # complete one per level to mark critical path progress
    r1 = TaskResult(task_id='t1', status='SUCCESS', result={}, duration=1.0, success=True)
    r2 = TaskResult(task_id='t2', status='SUCCESS', result={}, duration=1.0, success=True)
    # mark only first level fully complete
    state.tasks_completed = [r1]
    # critical path: only first level done -> done/total_levels *100
    cp = mon.calculate_critical_path_progress(state)
    assert 0.0 <= cp <= 100.0


def test_identify_bottleneck_and_retry_rate():
    mon = ExecutionMonitor()
    plan = make_plan_var([1,1])
    state = ExecutionState(plan=plan, start_time=datetime.now())
    # no completed -> no bottleneck
    state.tasks_completed = []
    assert mon.identify_bottleneck_tasks(state) == []
    # create long-running completed task
    tr = TaskResult(task_id='t1', status='SUCCESS', result={}, duration=35.0, success=True)
    state.tasks_completed = [tr]
    assert mon.identify_bottleneck_tasks(state) == ['t1']
    # retry rate with counts
    state.tasks_failed = []
    state.retry_counts = {'t1': 2}
    rr = mon.calculate_retry_rate(state)
    assert isinstance(rr, float)


def test_detect_anomalies_various():
    mon = ExecutionMonitor()
    plan = make_plan_var([1])
    state = ExecutionState(plan=plan, start_time=datetime.now())
    # in-progress with no start_time (uses default) -> no anomalies
    state.tasks_in_progress = [type('T', (), {'id':'x'})()]
    a = mon.detect_anomalies(state)
    assert isinstance(a, list)
    # in-progress exceeding timeout
    class InProg:
        def __init__(self):
            self.id = 't_long'
            self.start_time = datetime.now() - timedelta(seconds=200)
            self.timeout = 50
    state.tasks_in_progress = [InProg()]
    # create completed list to compute recent failure rate too
    fail = TaskResult(task_id='t_prev', status='FAIL', result={}, duration=1.0, success=False)
    state.tasks_completed = [fail] * 5
    anomalies = mon.detect_anomalies(state)
    types = [x.type for x in anomalies]
    assert ('EXCESSIVE_TIMEOUT' in types) or ('HIGH_FAILURE_RATE' in types)


def test_adaptive_replanner_behavior():
    repl = AdaptiveReplanner()
    plan = make_plan_var([2,1])
    state = ExecutionState(plan=plan, start_time=datetime.now())
    m = ExecutionMetrics()
    m.retry_rate = 0.35
    m.bottleneck_tasks = []
    m.estimated_remaining_time = 100
    assert repl.should_replan(state, m) is True
    changes = repl.identify_plan_changes(plan, m)
    assert 'reduce_parallelism' in changes
