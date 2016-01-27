from functools import partial, update_wrapper, WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES
from inspect import signature


def centaur_update_wrapper(wrapper, wrapped, assigned, updated):
    w = update_wrapper(wrapper, wrapped, assigned, updated)
    w.__signature__ = signature(wrapped)
    return w


def wraps_w_signature(wrapped,
                      assigned=WRAPPER_ASSIGNMENTS,
                      updated=WRAPPER_UPDATES):
    "A version of @wraps decorator witch keeps the function signature."
    return partial(centaur_update_wrapper, wrapped=wrapped,
                   assigned=assigned, updated=updated)


def call_in_ctx(ctx_dict, fn):
    return fn(**select_params_for_fn(ctx_dict, fn))


def select_params_for_fn(ctx_dict, fn):
    sign = signature(fn)
    return {k: v for k, v in ctx_dict.items() if k in sign.parameters}
