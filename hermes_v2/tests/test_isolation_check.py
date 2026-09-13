import pytest
from hermes_v2.isolation_check import is_path_isolated, is_import_isolated, is_config_isolated


def test_path_isolation():
    assert is_path_isolated('/Users/huchufan/project')
    assert not is_path_isolated('/etc/passwd')


def test_import_isolation():
    assert is_import_isolated('json')
    assert not is_import_isolated('os')


def test_config_isolation():
    cfg = {'endpoint':'http://example.com'}
    assert not is_config_isolated(cfg)
    assert is_config_isolated({'local':'value'})
