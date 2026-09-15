"""
Hermes Agent - 共享类型定义 (Shared Type Definitions)

所有六大框架 (governance / orchestration / memory / automation /
evolution / multiagent) 共用的数据模型、枚举与协议接口。

设计文档: 00_系统架构总览.md
创建时间: 2026-09-11
版本: 1.0
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------


def now() -> datetime:
    """返回带 UTC 时区的当前时间。"""
    return datetime.now(timezone.utc)


def generate_uuid(prefix: str = "") -> str:
    """生成唯一标识，可带前缀（如 audit- / agent-）。"""
    ident = uuid.uuid4().hex[:12]
    return f"{prefix}{ident}" if prefix else ident


# ---------------------------------------------------------------------------
# 通用枚举
# ---------------------------------------------------------------------------


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    WARN = "WARN"


class OperationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    RUNNING = "RUNNING"
    TIMEOUT = "TIMEOUT"
    RETRY = "RETRY"
    SCHEDULED = "SCHEDULED"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


# ---------------------------------------------------------------------------
# 治理框架类型 (Governance)
# ---------------------------------------------------------------------------


class Role(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    SERVICE = "service"
    GUEST = "guest"


class Permission(str, Enum):
    EXECUTE_AGENT = "agent:execute"
    EXECUTE_ANY = "agent:execute_any"
    EXECUTE_OWN = "agent:execute_own"
    EXECUTE_SCHEDULED = "agent:execute_scheduled"
    READ_MEMORY = "memory:read"
    WRITE_CONFIG = "config:write"
    READ_CONFIG = "config:read"
    MODIFY_SYSTEM = "config:modify_system"
    AUDIT_LOG = "audit:read"
    AUDIT_READ_ALL = "audit:read_all"
    AUDIT_READ_OWN = "audit:read_own"
    SKILL_CREATE = "skill:create"
    SKILL_EXECUTE = "skill:execute"
    SKILL_EXPLORE = "skill:explore"
    POLICY_MANAGE = "policy:manage"
    GATEWAY_WRITE = "gateway:write"
    QUERY_READONLY = "agent:query_readonly"
    DATA_EXPORT = "data:export"


@dataclass
class Actor:
    """操作发起者（用户 / 服务账户 / agent）。"""

    id: str = field(default_factory=generate_uuid)
    role: str = Role.USER.value
    organization: str = "default"
    permissions: List[str] = field(default_factory=list)
    clearance_level: int = 0
    session_id: Optional[str] = None


@dataclass
class Resource:
    """被访问的目标资源。"""

    type: str = "generic"
    id: str = field(default_factory=generate_uuid)
    owner: str = ""
    classification: str = "INTERNAL"
    sensitivity: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class ExecutionContext:
    """执行上下文（治理 / 编排 / 自动化共用）。"""

    request_id: str = field(default_factory=generate_uuid)
    source_ip: str = "127.0.0.1"
    gateway: str = "cli"
    use_encryption: bool = True
    network_security_level: str = "TLS-1.3"
    threat_level: str = "LOW"
    time: datetime = field(default_factory=now)
    location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessDecision:
    """访问控制决策结果。"""

    allow: bool = False
    reason: str = "Default deny"
    audit_code: str = "ACCESS_DENIED"
    requires_approval: bool = False
    approval_chain: List[str] = field(default_factory=list)


@dataclass
class Operation:
    """一次待治理校验的操作。"""

    action: str = ""
    actor: Optional[Actor] = None
    resource: Optional[Resource] = None
    context: Optional[ExecutionContext] = None
    estimated_duration: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult:
    """操作执行结果。"""

    status: str = OperationStatus.SUCCESS.value
    code: int = 0
    error: Optional[str] = None
    duration_ms: float = 0.0
    data: Any = None


@dataclass
class AuditRecord:
    """审计日志记录。"""

    audit_id: str = field(default_factory=lambda: generate_uuid("aud-"))
    timestamp: datetime = field(default_factory=now)
    actor_id: str = ""
    actor_role: str = ""
    actor_organization: str = ""
    operation_type: str = ""
    operation_status: str = ""
    resource_type: str = ""
    resource_id: str = ""
    resource_owner: str = ""
    action_details: str = ""
    source_ip: str = ""
    source_gateway: str = ""
    request_id: str = ""
    result_code: int = 0
    error_message: Optional[str] = None
    involves_sensitive_data: bool = False
    data_classification: str = "INTERNAL"
    encryption_used: bool = True
    network_security: str = ""
    changes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 编排框架类型 (Orchestration)
# ---------------------------------------------------------------------------


@dataclass
class IntentAnalysis:
    """意图识别结果。"""

    primary_intent: str = ""
    confidence: float = 0.0
    alternative_intents: List[Tuple[str, float]] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    requires_clarification: bool = False
    clarification_questions: List[str] = field(default_factory=list)


@dataclass
class ParameterDef:
    """参数定义。"""

    name: str = ""
    type: str = "string"
    description: str = ""
    default: Any = None
    required: bool = True


@dataclass
class Intent:
    """意图定义。"""

    name: str = ""
    keywords: List[str] = field(default_factory=list)
    required_parameters: List[ParameterDef] = field(default_factory=list)
    optional_parameters: List[ParameterDef] = field(default_factory=list)
    skills_involved: List[str] = field(default_factory=list)
    complexity: str = "low"


@dataclass
class ParameterSet:
    """参数提取结果。"""

    parameters: Dict[str, Any] = field(default_factory=dict)
    missing_required: List[str] = field(default_factory=list)
    complete: bool = True


@dataclass
class SubTask:
    """子任务。"""

    id: str = field(default_factory=generate_uuid)
    skill_name: str = ""
    description: str = ""
    depends_on: List[str] = field(default_factory=list)
    timeout: float = 60.0
    parallel_allowed: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    retry_policy: str = "exponential_backoff"


@dataclass
class ExecutionPlan:
    """执行计划。"""

    intent: Optional[Intent] = None
    subtasks: List[SubTask] = field(default_factory=list)
    parallel_groups: List[List[SubTask]] = field(default_factory=list)
    execution_order: List[List[SubTask]] = field(default_factory=list)
    resource_estimate: Dict[str, Any] = field(default_factory=dict)
    time_estimate: float = 0.0
    fallback_strategies: List[Any] = field(default_factory=list)
    contingency_plans: List[Any] = field(default_factory=list)

    @property
    def all_tasks(self) -> List[SubTask]:
        return self.subtasks


@dataclass
class TaskResult:
    """任务执行结果。"""

    task_id: str = ""
    status: str = OperationStatus.SUCCESS.value
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    success: bool = True


@dataclass
class ExecutionResult:
    """工作流 / 计划执行结果。"""

    status: str = OperationStatus.SUCCESS.value
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    tasks_executed: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    execution_id: str = field(default_factory=generate_uuid)


@dataclass
class ExecutionState:
    """执行状态跟踪。"""

    plan: Optional[ExecutionPlan] = None
    start_time: datetime = field(default_factory=now)
    tasks_completed: List[TaskResult] = field(default_factory=list)
    tasks_failed: List[TaskResult] = field(default_factory=list)
    tasks_in_progress: List[SubTask] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    retry_counts: Dict[str, int] = field(default_factory=dict)

    def get_retry_count(self, task_id: str) -> int:
        return self.retry_counts.get(task_id, 0)


@dataclass
class RecoveryAction:
    """恢复动作。"""

    action: str = "STOP"  # STOP / RETRY / FALLBACK / CONTINUE
    skip_dependents: bool = False
    fallback_skill: Optional[str] = None


@dataclass
class ExecutionMetrics:
    """执行监控指标。"""

    overall_progress: float = 0.0
    critical_path_progress: float = 0.0
    average_task_duration: float = 0.0
    parallelism_efficiency: float = 0.0
    resource_utilization: float = 0.0
    success_rate: float = 0.0
    retry_rate: float = 0.0
    bottleneck_tasks: List[str] = field(default_factory=list)
    estimated_remaining_time: float = 0.0


@dataclass
class Anomaly:
    """异常。"""

    type: str = ""
    severity: str = Severity.MEDIUM.value
    task_id: Optional[str] = None
    value: Any = None
    suggestion: str = ""


@dataclass
class Condition:
    """条件。"""

    type: str = "COMPARISON"
    left: Any = None
    right: Any = None
    operator: str = "=="
    children: List["Condition"] = field(default_factory=list)
    logic: str = "AND"


# ---------------------------------------------------------------------------
# 记忆框架类型 (Memory)
# ---------------------------------------------------------------------------


@dataclass
class ConversationTurn:
    """对话轮次。"""

    timestamp: datetime = field(default_factory=now)
    user_message: str = ""
    agent_response: str = ""
    user_intent: Optional[str] = None
    user_entities: Dict[str, Any] = field(default_factory=dict)
    response_intent: Optional[str] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """对话上下文。"""

    turns: List[ConversationTurn] = field(default_factory=list)
    main_topic: str = ""
    participant_intents: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    conversation_state: str = "idle"
    last_turn_time: Optional[datetime] = None


@dataclass
class AttentionContext:
    """注意力上下文。"""

    items: List[Any] = field(default_factory=list)
    primary: Any = None
    secondary: List[Any] = field(default_factory=list)
    focus_strength: float = 0.0


@dataclass
class SessionRecord:
    """会话记录。"""

    session_id: str = field(default_factory=generate_uuid)
    user_id: str = ""
    created_at: datetime = field(default_factory=now)
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_variables: Dict[str, Any] = field(default_factory=dict)
    session_goals: List[str] = field(default_factory=list)
    summary: str = ""
    key_decisions: List[str] = field(default_factory=list)
    message_count: int = 0
    duration: float = 0.0
    access_control: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContext:
    """会话上下文。"""

    session_id: str = ""
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    user_style: str = "neutral"
    technical_level: str = "intermediate"
    language: str = "zh"
    response_format: str = "plain"
    variables: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=now)


@dataclass
class UserProfile:
    """用户偏好画像。"""

    communication_style: str = "neutral"
    verbosity: float = 0.5
    formality: float = 0.5
    technical_level: str = "intermediate"
    jargon_preference: float = 0.5
    preferred_formats: List[str] = field(default_factory=list)
    code_snippet_preference: float = 0.5
    interested_topics: List[str] = field(default_factory=list)
    topic_expertise: Dict[str, float] = field(default_factory=dict)
    response_speed_preference: str = "balanced"


@dataclass
class SystemEvent:
    """系统事件。"""

    type: str = ""
    actor: str = ""
    action: str = ""
    resource: str = ""
    session_id: str = ""
    conversation_id: str = ""
    related_event_ids: List[str] = field(default_factory=list)
    result: Any = None
    success: bool = True
    error: Optional[str] = None
    consequences: List[str] = field(default_factory=list)


@dataclass
class EventRecord:
    """事件记录。"""

    event_id: str = field(default_factory=generate_uuid)
    timestamp: datetime = field(default_factory=now)
    event_type: str = ""
    actor: str = ""
    action: str = ""
    resource: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = True
    error: Optional[str] = None
    consequences: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class LearnedPattern:
    """学习到的模式。"""

    pattern_type: str = ""
    description: str = ""
    confidence: float = 0.5
    examples: List[Any] = field(default_factory=list)


@dataclass
class KnowledgeItem:
    """知识项。"""

    title: str = ""
    content: str = ""
    category: str = ""
    concepts: List[str] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    source: str = ""
    context: str = ""
    tags: List[str] = field(default_factory=list)
    domain: str = ""


@dataclass
class KnowledgeRecord:
    """知识记录。"""

    knowledge_id: str = field(default_factory=generate_uuid)
    title: str = ""
    content: str = ""
    category: str = ""
    concepts: List[str] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    source: str = ""
    embedding: List[float] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)
    access_count: int = 0
    relevance_score: float = 0.5
    tags: List[str] = field(default_factory=list)
    domain: str = ""


@dataclass
class SearchResult:
    """搜索结果。"""

    knowledge_id: str = ""
    title: str = ""
    summary: str = ""
    relevance_score: float = 0.0
    source: str = ""
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    layer: str = ""


@dataclass
class SearchQuery:
    """搜索查询。"""

    user_id: Optional[str] = None
    topic: str = ""
    date_range: Optional[Tuple[datetime, datetime]] = None
    min_relevance: float = 0.0
    limit: int = 10


@dataclass
class ArchiveReference:
    """档案引用。"""

    archive_id: str = field(default_factory=generate_uuid)
    session_id: str = ""
    archive_path: str = ""
    archived_at: datetime = field(default_factory=now)
    retention_period: timedelta = field(default_factory=lambda: timedelta(days=2555))
    user_id: str = ""
    date: Optional[Any] = None
    size: int = 0
    access_control: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""


@dataclass
class FusedResult:
    """融合结果。"""

    candidates: List[Any] = field(default_factory=list)
    fusion_method: str = "weighted_combination"


@dataclass
class FusedMemoryResult:
    """跨层记忆检索结果。"""

    layer_1: Any = None
    layer_2: List[Any] = field(default_factory=list)
    layer_3: List[Any] = field(default_factory=list)
    layer_4: List[Any] = field(default_factory=list)
    fused: Optional[FusedResult] = None


@dataclass
class UserHistory:
    """用户历史。"""

    user_id: str = ""
    sessions: List[SessionRecord] = field(default_factory=list)


@dataclass
class CapabilityProfile:
    """能力画像。"""

    strong_domains: List[str] = field(default_factory=list)
    weak_domains: List[str] = field(default_factory=list)
    technical_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    learning_speed: float = 0.5


@dataclass
class ComprehensiveUserModel:
    """综合用户模型。"""

    user_id: str = ""
    capability_profile: Any = None
    preference_profile: Any = None
    knowledge_profile: Any = None
    behavioral_profile: Any = None
    values_and_goals: Any = None


# ---------------------------------------------------------------------------
# 自动化框架类型 (Automation)
# ---------------------------------------------------------------------------


@dataclass
class Trigger:
    """触发器。"""

    trigger_id: str = field(default_factory=generate_uuid)
    trigger_type: str = (
        "manual"  # schedule/event/condition/manual/webhook/message/system
    )
    workflow_id: str = ""
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=now)


@dataclass
class TriggerRegistration:
    """触发器注册信息。"""

    trigger_id: str = ""
    workflow_id: str = ""
    trigger: Optional[Trigger] = None
    registered_at: datetime = field(default_factory=now)
    enabled: bool = True


@dataclass
class TriggerContext:
    """触发上下文。"""

    trigger_id: str = ""
    fired_at: datetime = field(default_factory=now)
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = ""


@dataclass
class Workflow:
    """工作流定义。"""

    id: str = field(default_factory=generate_uuid)
    name: str = ""
    tasks: List[SubTask] = field(default_factory=list)
    max_retries: int = 3
    timeout: float = 3600.0
    memory_requirement: float = 0.0
    cpu_requirement: float = 0.0
    priority: int = 50


@dataclass
class WorkflowExecution:
    """工作流执行实例。"""

    workflow_id: str = ""
    execution_id: str = field(default_factory=generate_uuid)
    trigger_id: str = ""
    triggered_at: datetime = field(default_factory=now)
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = OperationStatus.RUNNING.value
    result: Any = None


@dataclass
class ResourceEstimate:
    """资源估计。"""

    duration: float = 0.0
    memory: float = 0.0
    cpu: float = 0.0


@dataclass
class ScheduleJob:
    """调度任务。"""

    job_id: str = field(default_factory=generate_uuid)
    workflow_id: str = ""
    trigger_id: str = ""
    scheduled_time: datetime = field(default_factory=now)
    priority: int = 50
    estimated_duration: float = 0.0
    estimated_memory: float = 0.0
    estimated_cpu: float = 0.0
    max_retries: int = 3
    timeout: float = 3600.0
    status: str = OperationStatus.SCHEDULED.value
    created_at: datetime = field(default_factory=now)
    started_at: Optional[datetime] = None
    retries_remaining: int = 3


@dataclass
class JobResult:
    """调度任务结果。"""

    job_id: str = ""
    status: str = OperationStatus.SUCCESS.value
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    retries_remaining: int = 0


@dataclass
class ResourceSnapshot:
    """资源快照。"""

    cpu: float = 1.0
    memory: float = 1.0
    timestamp: datetime = field(default_factory=now)


@dataclass
class Worker:
    """执行工作进程。"""

    worker_id: str = field(default_factory=generate_uuid)
    available_memory: float = 1.0
    available_cpu: float = 1.0
    current_load: float = 0.0
    max_capacity: float = 1.0
    status: str = "healthy"
    tools: List[str] = field(default_factory=list)

    def has_required_tools(self, workflow: Workflow) -> bool:
        return True


# ---------------------------------------------------------------------------
# 自进化框架类型 (Evolution)
# ---------------------------------------------------------------------------


@dataclass
class ExecutionTrace:
    """执行轨迹。"""

    execution_id: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    resource_usage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionInsight:
    """执行洞察。"""

    execution_id: str = ""
    timestamp: datetime = field(default_factory=now)
    success_patterns: List[Any] = field(default_factory=list)
    failure_analysis: Any = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    resource_efficiency: float = 0.0
    decision_path: List[Any] = field(default_factory=list)


@dataclass
class SuccessFactors:
    """成功因素。"""

    skills_used: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    resource_usage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureAnalysis:
    """失败分析。"""

    error_type: str = ""
    root_cause: str = ""
    recovery_actions: List[str] = field(default_factory=list)
    recovery_success_rate: float = 0.0


@dataclass
class SuccessfulConfiguration:
    """成功配置。"""

    skill_selection: List[str] = field(default_factory=list)
    parameter_values: Dict[str, Any] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    resource_allocation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryPattern:
    """恢复模式。"""

    failure_type: str = ""
    root_cause: str = ""
    recovery_actions: List[str] = field(default_factory=list)
    effectiveness: float = 0.0


@dataclass
class ImpactAnalysis:
    """参数影响分析。"""

    param_name: str = ""
    correlation: float = 0.0
    optimal_value: Any = None


@dataclass
class ParameterConstraints:
    """参数约束。"""

    min_value: float = 0.0
    max_value: float = 1.0


@dataclass
class SkillDefinition:
    """技能定义。"""

    name: str = ""
    description: str = ""
    code: str = ""
    version: str = "0.1.0"
    created_from_pattern: str = ""
    quality_score: float = 0.0


@dataclass
class SkillImprovement:
    """技能改进机会。"""

    skill_id: str = ""
    target: str = ""
    training_examples: List[Any] = field(default_factory=list)
    type: str = "IMPROVE_EXISTING"


@dataclass
class SkillCreationOpportunity:
    """技能创建机会。"""

    skill_name: str = ""
    description: str = ""
    pattern: str = ""
    template: str = ""
    requirements: List[str] = field(default_factory=list)
    type: str = "CREATE_NEW_SKILL"


@dataclass
class SkillQualityMetrics:
    """技能质量指标。"""

    skill_id: str = ""
    functional_correctness: float = 0.0
    performance_efficiency: float = 0.0
    robustness: float = 0.0
    generalization_ability: float = 0.0
    documentation_quality: float = 0.0
    maintainability: float = 0.0
    overall_score: float = 0.0
    quality_tier: str = ""


@dataclass
class PerformanceAnalysis:
    """性能分析。"""

    critical_path_utilization: float = 0.0
    parallelism_efficiency: float = 0.0
    resource_utilization_variance: float = 0.0


@dataclass
class OrchestrationStrategy:
    """编排策略。"""

    name: str = ""
    dag_structure: Any = None
    parallelism_degree: int = 1
    resource_allocation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueueAnalysis:
    """队列分析。"""

    avg_memory: float = 0.0
    avg_wait_time: float = 0.0
    avg_priority: float = 0.0


@dataclass
class PriorityFunction:
    """优先级函数。"""

    name: str = ""


@dataclass
class BottleneckAnalysis:
    """瓶颈分析。"""

    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)

    def add_bottleneck(
        self, type: str, severity: str, potential_improvement: str
    ) -> None:
        self.bottlenecks.append(
            {
                "type": type,
                "severity": severity,
                "potential_improvement": potential_improvement,
            }
        )


@dataclass
class ArchitecturalImprovement:
    """架构改进。"""

    type: str = ""
    description: str = ""
    value_score: float = 0.0
    feasibility_score: float = 0.0


@dataclass
class UserFeedback:
    """用户反馈。"""

    type: str = "CORRECTION"  # CORRECTION / PREFERENCE / FEATURE_REQUEST / BUG_REPORT
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrectionFeedback:
    """纠正反馈。"""

    root_cause_type: str = ""
    content: str = ""
    related_skill: Optional[str] = None


# ---------------------------------------------------------------------------
# 多智能体框架类型 (Multi-Agent)
# ---------------------------------------------------------------------------


class AgentState(str, Enum):
    CREATED = "CREATED"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    BUSY = "BUSY"
    DEGRADED = "DEGRADED"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


@dataclass
class AgentConfig:
    """Agent 配置。"""

    role: str = "WORKER"
    capabilities: List[str] = field(default_factory=list)
    specialization: str = ""
    heartbeat_interval: int = 30
    heartbeat_timeout: int = 60
    max_concurrent_tasks: int = 10


@dataclass
class Agent:
    """Agent 实例。"""

    agent_id: str = field(default_factory=lambda: generate_uuid("agent-"))
    config: AgentConfig = field(default_factory=AgentConfig)
    state: str = AgentState.CREATED.value
    role: str = ""
    specialization: str = ""
    created_at: datetime = field(default_factory=now)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    heartbeat_failures: int = 0
    error_count: int = 0
    failure_count: int = 0
    uptime: float = 0.0
    failure_rate: float = 0.0
    available_cpu: float = 1.0
    available_memory: float = 1.0
    current_load: float = 0.0
    task_count: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    avg_response_time: float = 0.0
    task_queue: List[Any] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)

    def get_average_response_time(self) -> float:
        return self.avg_response_time

    def get_success_rate(self) -> float:
        total = self.completed_tasks + self.failed_tasks
        if total == 0:
            return 1.0
        return self.completed_tasks / total

    def get_available_resources(self) -> ResourceSnapshot:
        return ResourceSnapshot(cpu=self.available_cpu, memory=self.available_memory)


@dataclass
class AgentHeartbeat:
    """Agent 心跳。"""

    agent_id: str = ""
    timestamp: datetime = field(default_factory=now)
    state: str = ""
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    task_count: int = 0
    error_count: int = 0


@dataclass
class AgentHealthStatus:
    """Agent 健康状态。"""

    agent_id: str = ""
    check_time: datetime = field(default_factory=now)
    connectivity: bool = True
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    queue_status: Dict[str, Any] = field(default_factory=dict)
    error_rate: float = 0.0
    response_time: float = 0.0
    overall_health: str = "HEALTHY"


@dataclass
class AgentMessage:
    """Agent 消息。"""

    message_id: str = field(default_factory=generate_uuid)
    from_agent: str = ""
    to_agents: List[str] = field(default_factory=list)
    message_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=now)
    priority: str = "NORMAL"


@dataclass
class RPCRequest:
    """RPC 请求。"""

    request_id: str = field(default_factory=generate_uuid)
    from_agent: str = ""
    to_agent: str = ""
    method: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=now)


@dataclass
class RPCResponse:
    """RPC 响应。"""

    request_id: str = ""
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class Task:
    """多智能体任务。"""

    task_id: str = field(default_factory=generate_uuid)
    task_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: str = "MEDIUM"
    deadline: Optional[datetime] = None
    status: str = "PENDING"
    failure_count: int = 0
    max_retries: int = 3
    estimated_resources: ResourceSnapshot = field(default_factory=ResourceSnapshot)
    required_skills: List[str] = field(default_factory=list)
    decomposition_strategy: str = "SEQUENTIAL"


@dataclass
class SubTaskResult:
    """子任务结果。"""

    task_id: str = ""
    status: str = OperationStatus.SUCCESS.value
    data: Any = None
    error: Optional[str] = None


@dataclass
class TaskCoordination:
    """任务协调上下文。"""

    parent_task_id: str = ""
    subtasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)
    assigned_agents: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentInfo:
    """Agent 注册信息。"""

    id: str = field(default_factory=generate_uuid)
    role: str = "WORKER"
    capabilities: List[str] = field(default_factory=list)
    specialization: str = ""
    state: str = AgentState.RUNNING.value
    address: str = ""


@dataclass
class LoadDistribution:
    """负载分布。"""

    overloaded_agents: List[str] = field(default_factory=list)
    underloaded_agents: List[str] = field(default_factory=list)
    avg_load: float = 0.0
    std_dev: float = 0.0
    imbalance_factor: float = 0.0


@dataclass
class ClusterMetrics:
    """集群指标。"""

    total_agents: int = 0
    running_agents: int = 0
    failed_agents: int = 0
    avg_cpu_usage: float = 0.0
    avg_memory_usage: float = 0.0
    avg_load: float = 0.0
    avg_response_time: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0


@dataclass
class OptimizationOpportunity:
    """优化机会。"""

    type: str = ""
    current_metric: float = 0.0
    potential_improvement: float = 0.0
    agent_id: Optional[str] = None
    impact: float = 0.0
    effort: str = "MEDIUM"


@dataclass
class PerformanceSnapshot:
    """性能快照。"""

    timestamp: datetime = field(default_factory=now)
    metrics: Dict[str, Any] = field(default_factory=dict)
