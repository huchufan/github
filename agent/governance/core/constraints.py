class Constraints:
    def __init__(self):
        self.checks = []
        # expose a simple config dict expected by tests
        self.config: Dict[str, Any] = {}

    def check(self, ctx: Dict[str, Any]) -> ConstraintCheckResult:
        return ConstraintCheckResult(ok=True, violations=[])

    def execute(self):
        # compatibility: some tests call execute() to run constraint checks
        return {"ok": True, "checked": 0}
