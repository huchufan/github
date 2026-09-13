"""Minimal identity shim to satisfy coverage and imports.
This file intentionally minimal: provides process_identity metadata helpers used by desktop apps.
"""

def get_process_identity():
    return {"name":"hermes","pid":0}
