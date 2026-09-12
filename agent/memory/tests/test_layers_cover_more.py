import pytest
from datetime import datetime, timedelta

from agent.memory.core.layers import (
    LRUCache,
    ImmediateContextMemory,
    SessionMemory,
    EpisodicMemory,
    ArchiveMemory,
)
from agent.core.types import SessionRecord, SystemEvent


def test_lru_cache_eviction_and_contains():
    c = LRUCache(size=2)
    c.put('a', 1)
    c.put('b', 2)
    assert 'a' in c and 'b' in c
    # adding c evicts 'a'
    c.put('c', 3)
    assert 'a' not in c
    assert 'c' in c and 'b' in c
    # access b moves it to end; adding d evicts c
    assert c.get('b') == 2
    c.put('d', 4)
    assert 'c' not in c


def test_immediate_context_conversation_and_attention():
    m = ImmediateContextMemory(max_size=3)
    t1 = m.record_conversation_turn('hello', 'hi')
    t2 = m.record_conversation_turn('how are you', 'fine')
    ctx = m.get_conversation_context(window_size=2)
    assert ctx.conversation_state == 'active'
    assert ctx.last_turn_time is not None
    # update execution state
    m.update_execution_state({'step': 1})
    assert m.execution_state.get('step') == 1
    # attention stack
    m.attention_stack = ['focus', 'a', 'b']
    ac = m.get_attention_context()
    assert ac.primary == 'focus'
    assert ac.secondary == ['a', 'b']
    assert ac.focus_strength == pytest.approx(1.0 / 3.0)


def test_session_memory_store_retrieve_and_expiry():
    sm = SessionMemory()
    rec = SessionRecord(session_id='s1', user_id='u1')
    sm.store('s1', rec)
    got = sm.retrieve('s1')
    assert isinstance(got, SessionRecord)
    # simulate expiry by setting created_at in the past
    sm.created_at['s1'] = datetime.now() - timedelta(days=31)
    got2 = sm.retrieve('s1')
    assert got2 is None


def test_episodic_record_and_learned_patterns():
    em = EpisodicMemory()
    ev1 = SystemEvent(type='job', actor='a', action='run', resource='r', session_id='s', conversation_id='c', result={}, success=True)
    ev2 = SystemEvent(type='job', actor='a', action='run', resource='r', session_id='s', conversation_id='c', result={}, success=True)
    ev3 = SystemEvent(type='job', actor='b', action='fail', resource='r', session_id='s', conversation_id='c', result={}, success=False, error='err')
    em.record_event(ev1)
    em.record_event(ev2)
    em.record_event(ev3)
    patterns = em.extract_learned_patterns(time_window=timedelta(days=365))
    assert any(p.pattern_type in ('success_sequence', 'failure_recovery') for p in patterns)


def test_archive_and_retrieve_session_roundtrip():
    am = ArchiveMemory()
    s = SessionRecord(session_id='sess-123', user_id='u123')
    ref = am.archive_session(s)
    assert ref.archive_path.startswith('archive://')
    # retrieve
    got = am.retrieve_archived_session(ref.archive_id)
    assert isinstance(got, SessionRecord)
    assert got.session_id == s.session_id
