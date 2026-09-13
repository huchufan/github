def is_path_isolated(path: str) -> bool:
    # minimal check: path should not be under system dirs like /etc, /usr
    forbidden = ['/etc', '/usr', '/bin', '/sbin', '/var']
    return not any(path.startswith(p) for p in forbidden)


def is_import_isolated(module_name: str) -> bool:
    # minimal check: module is not one of blocked builtins
    blocked = ['os', 'sys', 'subprocess']
    return module_name not in blocked


def is_config_isolated(config_dict: dict) -> bool:
    # minimal check: ensure no remote endpoints keys are present
    for k,v in config_dict.items():
        if isinstance(v, str) and (v.startswith('http://') or v.startswith('https://')):
            return False
    return True
