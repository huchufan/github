"""
Hermes Agent - 共享异常定义 (Shared Exceptions)

所有六大框架共用的异常层次结构，便于统一的错误处理与审计追踪。

设计文档: 00_系统架构总览.md
"""


class HermesError(Exception):
    """所有 Hermes 异常的基类。"""
    code: str = "HERMES_ERROR"

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# 治理框架异常
# ---------------------------------------------------------------------------

class AccessDeniedError(HermesError):
    code = "ACCESS_DENIED"


class PolicyViolationError(HermesError):
    code = "POLICY_VIOLATION"


class ConstraintViolationError(HermesError):
    code = "CONSTRAINT_VIOLATION"


class QuotaExceededError(HermesError):
    code = "QUOTA_EXCEEDED"


# ---------------------------------------------------------------------------
# 编排框架异常
# ---------------------------------------------------------------------------

class ExecutionFailedError(HermesError):
    code = "EXECUTION_FAILED"

    def __init__(self, message: str = "", failed_tasks=None):
        super().__init__(message)
        self.failed_tasks = failed_tasks or []


class ParameterValidationError(HermesError):
    code = "PARAMETER_VALIDATION"

    def __init__(self, parameter: str = "", reason: str = ""):
        super().__init__(f"Parameter '{parameter}' invalid: {reason}")
        self.parameter = parameter
        self.reason = reason


class TaskTimeoutError(HermesError):
    code = "TASK_TIMEOUT"


class DependencyMissingError(HermesError):
    code = "DEPENDENCY_MISSING"


class PreCheckFailedError(HermesError):
    code = "PRECHECK_FAILED"


# ---------------------------------------------------------------------------
# 记忆框架异常
# ---------------------------------------------------------------------------

class ArchiveCorruptedError(HermesError):
    code = "ARCHIVE_CORRUPTED"


class MemoryNotFoundError(HermesError):
    code = "MEMORY_NOT_FOUND"


# ---------------------------------------------------------------------------
# 自动化框架异常
# ---------------------------------------------------------------------------

class TriggerValidationError(HermesError):
    code = "TRIGGER_VALIDATION"


class WorkflowNotFoundError(HermesError):
    code = "WORKFLOW_NOT_FOUND"


class NoAvailableWorkersError(HermesError):
    code = "NO_AVAILABLE_WORKERS"


# ---------------------------------------------------------------------------
# 多智能体框架异常
# ---------------------------------------------------------------------------

class AgentStateError(HermesError):
    code = "AGENT_STATE_ERROR"


class AgentNotFoundError(HermesError):
    code = "AGENT_NOT_FOUND"


class AgentAlreadyRegisteredError(HermesError):
    code = "AGENT_ALREADY_REGISTERED"


class InvalidAgentInfoError(HermesError):
    code = "INVALID_AGENT_INFO"


class InsufficientCapabilityError(HermesError):
    code = "INSUFFICIENT_CAPABILITY"


class RoleLimitExceededError(HermesError):
    code = "ROLE_LIMIT_EXCEEDED"


class NoAvailableAgentError(HermesError):
    code = "NO_AVAILABLE_AGENT"


class RPCError(HermesError):
    code = "RPC_ERROR"


class RPCTimeoutError(HermesError):
    code = "RPC_TIMEOUT"
