import inspect
from centaur.utils import wraps_w_signature

from .defaults import _create_default_ctx
from .classes import _Datatype
from .context import _Module, _Context


def validate_before_call(param, **kwargs):
    _ctx, _kwargs = _create_default_ctx(), {}

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
        if isinstance(p.annotation, _Datatype):
            return p.annotation
        elif isinstance(p.annotation, dict):
            return _ctx.def_datatype(p.annotation)
        else:
            return _ctx[p.annotation]

    def _datatype_from_kwargs(p):
        if isinstance(_kwargs[p], _Datatype):
            return _kwargs[p]
        elif isinstance(_kwargs[p], dict):
            return _ctx.def_datatype(_kwargs[p])
        else:
            return _ctx[_kwargs[p]]

    def _not_default_params_with_validation(sig, ba):
        for param in sig.parameters.values():
            if _param_is_not_empty(param) and _param_is_not_default(param, ba):
                dt_from_annotation = _datatype_from_annotation(param)
                if dt_from_annotation is not None:
                    yield param, dt_from_annotation
            elif param in _kwargs and _param_is_not_default(param, ba):
                dt_from_kwargs = _datatype_from_kwargs(param)
                if dt_from_kwargs is not None:
                    yield param, dt_from_kwargs

    def _validate_fn_params_by_annotations(fn, *args, **kwargs):
        sig = inspect.signature(fn)
        bound_arguments = _add_default_param_values(sig.bind(*args, **kwargs), sig)
        validation_results = [
            datatype_.guard(
                bound_arguments.arguments[param.name])
            for param, datatype_ in _not_default_params_with_validation(sig, bound_arguments)]
        return validation_results

    def _decorator(fn):
        @wraps_w_signature(fn)
        def wrapper(*args, **kwargs):
            _validate_fn_params_by_annotations(fn, *args, **kwargs)
            result = fn(*args, **kwargs)
            return result
        return wrapper
    if callable(param):
        return _decorator(param)
    else:
        if isinstance(param, _Module):
            _ctx, _kwargs = param.ctx, kwargs  # noqa
        elif isinstance(param, _Context):
            _ctx, _kwargs = param, kwargs
        return _decorator
