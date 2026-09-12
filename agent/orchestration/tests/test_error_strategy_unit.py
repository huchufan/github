import asyncio
from agent.orchestration.core.executor import ErrorHandlingStrategy
from agent.core.types import SubTask


class RateLimitError(Exception):
    pass


def test_categorize_error_types():
    s = ErrorHandlingStrategy()
    assert s.categorize_error(asyncio.TimeoutError()) == "TIMEOUT"
    assert s.categorize_error(RateLimitError()) == "NETWORK_ERROR"
    assert s.categorize_error(Exception('x')) == "GENERIC_ERROR"


def test_select_recovery_strategy_retries_exhausted():
    s = ErrorHandlingStrategy(default_strategy='retry_on_transient')
    task = SubTask(id='t1', skill_name='s')
    # for retry_on_transient retries = 3, so if retry_count >=3 should return STOP
    strat = s.select_recovery_strategy(task, 'TIMEOUT', retry_count=3)
    assert strat.get('action') == 'STOP' or strat.get('action') == 'STOP'


def test_get_recovery_action_fields():
    s = ErrorHandlingStrategy()
    strategy = {'action': 'FALLBACK', 'fallback_skill': 'alt'}
    ra = s.get_recovery_action(strategy)
    assert ra.action == 'FALLBACK'
    assert ra.fallback_skill == 'alt'
