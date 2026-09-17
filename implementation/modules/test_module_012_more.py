
import importlib

def test_more_module_012():
    m = importlib.import_module('implementation.modules.module_012')
    # numeric positive
    out1 = m.format_output(m.compute(m.parse_input({'value': 5})))
    assert out1['status'] in ('ok','partial')
    # numeric negative
    out2 = m.format_output(m.compute(m.parse_input({'value': -3})))
    assert out2['payload']['result'] == 3
    # zero
    out3 = m.format_output(m.compute(m.parse_input({'value': 0})))
    assert out3['payload']['result'] == 0
    # list
    out4 = m.format_output(m.compute(m.parse_input([1,2,3])))
    assert out4['payload']['result'] == 3
