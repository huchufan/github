# compatibility additions
class RuleDecision:
    def __init__(self, decision: str = 'ALLOW'):
        self.decision = decision

__all__ = ['Policy', 'PolicyCondition', 'PolicyLimit', 'PolicyValidator', 'PolicyViolation', 'RuleEngine', 'ValidationResult', 'RuleDecision']
