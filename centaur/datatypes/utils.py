from copy import deepcopy


def without_items(dict_, keys):
    return {k: v for k, v in dict_.items() if k not in keys}


def with_items(dict_, keys):
    return {k: v for k, v in dict_.items() if k in keys}


def select_items(dict_, keys):
    return [dict_[k] for k in keys]


def deep_merge(d1, d2):
    ret = deepcopy(d1)
    for k, v in d2.items():
        if k in ret and isinstance(ret[k], dict):
            ret[k] = deep_merge(ret[k], v)
        else:
            ret[k] = deepcopy(v)
    return ret
