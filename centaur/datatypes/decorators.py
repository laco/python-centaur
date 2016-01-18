import functools
import inspect

from .defaults import _create_default_ctx
from .classes import _Datatype
from .functions import fulfill


def validate_before_call(param, *args):
    _ctx, _args = _create_default_ctx(), None

    def _add_default_param_values(ba, sig):
        for param in sig.parameters.values():
            if param.name not in ba.arguments:
                ba.arguments[param.name] = param.default
        return ba

    def _param_is_not_empty(p):
        return p.annotation is not inspect._empty

    def _param_is_not_default(p, ba):
        return ba.arguments[p.name] != p.default

    def _datatype_from_annotation(p):
        if isinstance(p.annotation, (_Datatype, dict)):
            return _Datatype.ensure_datatype(p.annotation)
        else:
            return _ctx.get_datatype(p.annotation)

    def _not_default_params_with_validation(sig, ba):
        for param in sig.parameters.values():
            if _param_is_not_empty(param) and _param_is_not_default(param, ba):
                dt_from_annotation = _datatype_from_annotation(param)
                if dt_from_annotation is not None:
                    yield param, dt_from_annotation

    def _validate_fn_params_by_annotations(fn, *args, **kwargs):
        sig = inspect.signature(fn)
        bound_arguments = _add_default_param_values(sig.bind(*args, **kwargs), sig)
        validation_results = [
            fulfill(
                bound_arguments.arguments[param.name],
                datatype_)
            for param, datatype_ in _not_default_params_with_validation(sig, bound_arguments)]
        return validation_results

    def _decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            _validate_fn_params_by_annotations(fn, *args, **kwargs)
            result = fn(*args, **kwargs)
            return result
        return wrapper
    if callable(param):
        return _decorator(param)
    else:
        _ctx, _args = param, args  # noqa
        return _decorator
