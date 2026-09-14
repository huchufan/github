# Patch: add missing ExecutionPlan reference and monitor helpers
from typing import Any, Dict, Optional
from agent.core.types import ExecutionPlan, ExecutionMetrics, TaskResult, ExecutionState, SubTask

class Monitor:
    """Monitor module (PoC)"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def execute(self, *args, **kwargs) -> Any:
        return {"module": "monitor", "ok": True}

class ExecutionMonitor:
    def __init__(self):
        self.events = []

    def record(self, evt: Dict[str, Any]):
        self.events.append(evt)

    def calculate_avg_duration(self, durations):
        if not durations:
            return 0.0
        return sum(durations)/len(durations)

    def identify_bottleneck_tasks(self, state: ExecutionState):
        # PoC: return tasks with duration > 30
        return [t.task_id for t in state.tasks_completed if getattr(t, 'duration', 0) > 30]

    def calculate_parallelism_efficiency(self, state: ExecutionState):
        # PoC: if no tasks completed, efficiency 0
        if not getattr(state, 'tasks_completed', []):
            return 0.0
        return 1.0

    def calculate_critical_path_progress(self, state: ExecutionState):
        # PoC: compute percent complete by completed tasks/total
        total = len(state.plan.subtasks) if state.plan else 0
        if total == 0:
            return 0.0
        completed = len(state.tasks_completed)
        return (completed/total)*100.0

    def detect_anomalies(self, state: ExecutionState):
        anomalies = []
        # find long-running tasks
        for t in getattr(state, 'tasks_in_progress', []):
            start = getattr(t, 'start_time', None)
            timeout = getattr(t, 'timeout', None)
            if start and timeout and (ExecutionMonitor._now_seconds() - start.timestamp()) > timeout:
                anomalies.append({'type':'TIMEOUT','task_id':getattr(t,'id',None)})
        return anomalies

    @staticmethod
    def _now_seconds():
        import time
        return time.time()

class AdaptiveReplanner:
    def __init__(self):
        pass

    def should_replan(self, execution_state: 'ExecutionState', metrics: 'ExecutionMetrics') -> bool:
        try:
            if metrics is None:
                return False
            if getattr(metrics, 'retry_rate', 0.0) > 0.3:
                return True
            if getattr(metrics, 'bottleneck_tasks', None):
                return True
            if getattr(metrics, 'estimated_remaining_time', 0.0) > 3600:
                return True
        except Exception:
            return False
        return False

    def identify_plan_changes(self, plan: ExecutionPlan, metrics: ExecutionMetrics):
        # PoC: return a simple re-ordered execution_order
        return []

    async def replan_if_needed(self, execution_state: 'ExecutionState', metrics: 'ExecutionMetrics') -> Optional['ExecutionPlan']:
        if execution_state is None or getattr(execution_state, 'plan', None) is None:
            return None
        plan = execution_state.plan
        if not self.should_replan(execution_state, metrics):
            return None
        # create shallow copy
        new_plan = ExecutionPlan(
            intent=plan.intent,
            subtasks=list(plan.subtasks),
            parallel_groups=list(plan.parallel_groups) if getattr(plan, 'parallel_groups', None) else [],
            execution_order=list(getattr(plan,'execution_order',[])),
            time_estimate=getattr(plan,'time_estimate',0.0),
            resource_estimate=getattr(plan,'resource_estimate',{}),
            fallback_strategies=getattr(plan,'fallback_strategies',[]),
            contingency_plans=getattr(plan,'contingency_plans',[]),
        )
        return new_plan

__all__ = ['Monitor', 'ExecutionMonitor', 'AdaptiveReplanner']
