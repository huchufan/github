"""
Auto-generated test for search
"""
import pytest
from agent.memory.core.search import Search


def test_search_init():
    inst = Search()
    assert inst.config == {}


def test_search_execute():
    inst = Search()
    r = inst.execute()
    assert r.get('ok') is True
