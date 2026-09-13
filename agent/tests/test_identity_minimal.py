import pytest

from agent.identity import get_process_identity


def test_get_process_identity_minimal():
    pid = get_process_identity()
    assert isinstance(pid, dict)
    assert pid.get('name') == 'hermes'
