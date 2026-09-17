


# AUTO_IMPL_MORE_START
# Enhanced auto implementation: input validation, multiple branches, error paths
def parse_input(payload=None):
    if payload is None:
        return {'value': None}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, (list, tuple)):
        # try to convert list of pairs
        try:
            return dict(payload)
        except Exception:
            return {'value': payload}
    try:
        return {'value': payload}
    except Exception:
        return {'value': None}

def compute(data=None):
    if data is None:
        return {'result': None, 'ok': False}
    # numeric path
    if isinstance(data, dict) and 'value' in data and isinstance(data['value'], (int, float)):
        v = data['value']
        if v < 0:
            return {'result': v * -1, 'note': 'abs', 'ok': True}
        elif v == 0:
            return {'result': 0, 'note': 'zero', 'ok': True}
        else:
            return {'result': v * 2, 'note': 'double', 'ok': True}
    # list path
    if isinstance(data, (list, tuple)):
        return {'result': len(data), 'ok': True}
    # fallback
    return {'result': str(data), 'ok': False}

def format_output(result=None):
    return {'status': 'ok' if isinstance(result, dict) and result.get('ok') else 'partial', 'payload': result}
# AUTO_IMPL_MORE_END
