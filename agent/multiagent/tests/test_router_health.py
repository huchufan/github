def test_run_health_check_once_smoke():
    from agent.multiagent import router

    res = router.run_health_check_once()
    assert isinstance(res, dict)
    # expect keys for T1..T0 at least
    assert "T1" in res
    assert "T0" in res
