from centaur.utils import wraps_w_signature
from functools import partial
from inspect import getcallargs


def curry(fn):
    def _all_required_params_present(fn, *args, **kwargs):
        try:
            getcallargs(fn, *args, *kwargs)
            return True
        except TypeError:
            return False

    @wraps_w_signature(fn)
    def wrapper(*args, **kwargs):
        if _all_required_params_present(fn, *args, **kwargs):
            return fn(*args, **kwargs)
        else:
            return partial(fn, *args, **kwargs)

    return wrapper
