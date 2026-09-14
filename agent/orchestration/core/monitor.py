# Patch: add missing ExecutionPlan reference and monitor helpers
from typing import Any, Dict, Optional
from agent.core.types import ExecutionPlan, ExecutionMetrics, TaskResult, ExecutionState, SubTask, Anomaly, Severity

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
        # durations may be TaskResult objects; extract .duration when present
        vals = []
        for d in durations:
            if hasattr(d, 'duration'):
                vals.append(getattr(d, 'duration', 0.0))
            elif isinstance(d, (int, float)):
                vals.append(d)
        if not vals:
            return 0.0
        return sum(vals)/len(vals)

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

    def monitor_execution(self, state: 'ExecutionState') -> 'ExecutionMetrics':
        metrics = ExecutionMetrics()
        # overall progress based on critical path
        metrics.overall_progress = self.calculate_critical_path_progress(state)
        metrics.bottleneck_tasks = self.identify_bottleneck_tasks(state)
        metrics.retry_rate = self.calculate_retry_rate(state) if hasattr(self, 'calculate_retry_rate') else 0.0
        # success rate
        success_count = len([t for t in getattr(state, 'tasks_completed', []) if getattr(t, 'success', False)])
        total_completed = max(1, len(getattr(state, 'tasks_completed', [])))
        metrics.success_rate = (success_count / total_completed) * 100.0
        return metrics

    def _recent_failure_rate(self, state: ExecutionState, window: int = 60) -> float:
        """Return fraction of failures in the last `window` seconds (PoC uses counts only)."""
        completed = getattr(state, 'tasks_completed', []) or []
        failed = getattr(state, 'tasks_failed', []) or []
        total = max(1, len(completed) + len(failed))
        return len(failed) / total

    def calculate_retry_rate(self, state: 'ExecutionState') -> float:
        # simple ratio: sum retries / total tasks attempted
        retry_counts = getattr(state, 'retry_counts', {}) or {}
        total_retries = sum(retry_counts.values())
        total_tasks = max(1, len(getattr(state, 'tasks_completed', [])) + len(getattr(state, 'tasks_failed', [])))
        return total_retries / total_tasks

    def estimate_remaining_time(self, state: 'ExecutionState') -> float:
        avg = self.calculate_avg_duration(state.tasks_completed)
        remaining_levels = max(0, len(getattr(state.plan, 'execution_order', [])) - len(getattr(state, 'tasks_completed', [])))
        # assume each remaining level takes avg * 60 for PoC
        return avg * remaining_levels * 60

    def detect_anomalies(self, state: 'ExecutionState'):
        anomalies = []
        # find long-running tasks
        for t in getattr(state, 'tasks_in_progress', []):
            start = getattr(t, 'start_time', None)
            timeout = getattr(t, 'timeout', None)
            if start and timeout and (ExecutionMonitor._now_seconds() - start.timestamp()) > timeout:
                anomalies.append(Anomaly(type='EXCESSIVE_TIMEOUT', severity=Severity.HIGH.value, task_id=getattr(t, 'id', None), suggestion='Investigate task timeout'))
        # high failure rate
        completed = getattr(state, 'tasks_completed', [])
        failed = getattr(state, 'tasks_failed', [])
        if len(completed) + len(failed) >= 5:
            recent_failure_rate = len(failed) / max(1, len(completed) + len(failed))
            if recent_failure_rate > 0.5:
                anomalies.append(Anomaly(type='HIGH_FAILURE_RATE', severity=Severity.HIGH.value, suggestion='High recent failure rate'))
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
            # retry rate or explicit bottlenecks always trigger
            if getattr(metrics, 'retry_rate', 0.0) > 0.3:
                return True
            if getattr(metrics, 'bottleneck_tasks', None):
                return True
            # if estimated remaining time is many times larger than original plan estimate
            plan_est = getattr(getattr(execution_state, 'plan', None), 'time_estimate', 0.0)
            if plan_est and getattr(metrics, 'estimated_remaining_time', 0.0) > (plan_est * 2):
                return True
        except Exception:
            return False
        return False

    def identify_plan_changes(self, plan: ExecutionPlan, metrics: ExecutionMetrics):
        changes = []
        if getattr(metrics, 'retry_rate', 0.0) > 0.3:
            changes.append('reduce_parallelism')
        if getattr(metrics, 'bottleneck_tasks', None):
            changes.append('reassign_bottleneck')
        return changes

    async def replan_if_needed(self, execution_state: 'ExecutionState', metrics: 'ExecutionMetrics') -> Optional['ExecutionPlan']:
        if execution_state is None or getattr(execution_state, 'plan', None) is None:
            return None
        plan = execution_state.plan
        if not self.should_replan(execution_state, metrics):
            return None
        # shallow copy
        new_plan = ExecutionPlan(
            intent=plan.intent,
            subtasks=list(plan.subtasks),
            parallel_groups=list(plan.parallel_groups) if getattr(plan, 'parallel_groups', None) else [],
            execution_order=list(getattr(plan, 'execution_order', [])),
            time_estimate=getattr(plan, 'time_estimate', 0.0),
            resource_estimate=getattr(plan, 'resource_estimate', {}),
            fallback_strategies=getattr(plan, 'fallback_strategies', []),
            contingency_plans=getattr(plan, 'contingency_plans', []),
        )
        # if retry rate high, flatten to single-task levels (reduce parallelism)
        if getattr(metrics, 'retry_rate', 0.0) > 0.4:
            new_plan.execution_order = [[t] for t in new_plan.subtasks]
        return new_plan

__all__ = ['Monitor', 'ExecutionMonitor', 'AdaptiveReplanner']
