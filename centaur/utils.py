from functools import partial, update_wrapper, WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES
from inspect import signature
from copy import deepcopy


def wraps_w_signature(wrapped,
                      assigned=WRAPPER_ASSIGNMENTS,
                      updated=WRAPPER_UPDATES):
    "A version of @wraps decorator witch keeps the function signature."

    def _centaur_update_wrapper(wrapper, wrapped, assigned, updated):
        w = update_wrapper(wrapper, wrapped, assigned, updated)
        w.__signature__ = signature(wrapped)
        return w

    return partial(_centaur_update_wrapper, wrapped=wrapped,
                   assigned=assigned, updated=updated)


def call_in_ctx(ctx_dict, fn):
    return fn(**select_params_for_fn(ctx_dict, fn))


def select_params_for_fn(ctx_dict, fn):
    sign = signature(fn)
    return {k: v for k, v in ctx_dict.items() if k in sign.parameters}


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


def create_ids(prefix, counter=0):
    counter_ = counter
    prefix_ = prefix

    def generate_id():
        nonlocal counter_
        ret = "{prefix}{counter}".format(prefix=prefix_, counter=counter_)
        counter_ += 1
        return ret
    return generate_id


class IDGenerator(object):
    def __init__(self, create_fn=create_ids):
        self.generators = {}
        self.create_fn = create_fn

    def generate_id(self, prefix):
        if prefix not in self.generators:
            self.generators[prefix] = self.create_fn(prefix)
        return self.generators[prefix]()


def fill_defaults(dict_, defaults, keep_nones=False):
    def _iter_keys_once(dicts):
        _yielded = []
        for d in dicts:
            for k in d.keys():
                if k not in _yielded:
                    _yielded.append(k)
                    yield k

    def _test_key_in_dict_and_not_none(dict_, key):
        return key in dict_ and dict_[key] is not None

    def _test_key_in_dict_allow_none(dict_, key):
        return key in dict_

    def _fill_defaults(dict_, defaults, _key_present_predicate):
        return {k: dict_[k] if _key_present_predicate(dict_, k) else defaults[k] for k in _iter_keys_once([dict_, defaults])}

    predicate_ = _test_key_in_dict_allow_none if keep_nones else _test_key_in_dict_and_not_none
    return _fill_defaults(dict_, defaults, _key_present_predicate=predicate_)
