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


class _Lazy(object):
    def __init__(self, callable_, *args, **kwargs):
        self._lazy_callable_ = callable_
        self._lazy_args = args
        self._lazy_kwargs = kwargs
        self._lazy_called = False

    def __eq__(self, other):
        return self._val.__eq__(other)

    @property
    def _val(self):
        if not self._lazy_called:
            self._lazy_obj = self._lazy_callable_(*self._lazy_args, **self._lazy_kwargs)
            self._lazy_called = True
        return self._lazy_obj

    # def __getattribute__(self, name):
    #     try:
    #         print(name)
    #         return super().__getattribute__(name)
    #     except AttributeError:
    #         return self._lazy_val(name)


def lazy(fn):
    @wraps_w_signature(fn)
    def wrapper(*args, **kwargs):
        return _Lazy(fn, *args, **kwargs)
    return wrapper


def compose(*fns):
    def wrapper(*args, **kwargs):
        return compose(*fns[:-1])((fns[-1](*args, **kwargs)))

    def identity(x):
        return x

    if len(fns) >= 1:
        return wraps_w_signature(fns[-1])(wrapper)
    else:
        return identity
