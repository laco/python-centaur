import inspect
from centaur.utils import wraps_w_signature


def validate_args_with_ctx(ctx=None, **kwargs):

    def _add_default_param_values(ba, sig):
        for param in sig.parameters.values():
            if param.name not in ba.arguments:
                ba.arguments[param.name] = param.default
        return ba

    def _param_is_not_empty(p):
        return p.annotation is not inspect._empty

    def _param_is_not_default(p, ba):
        return ba.arguments[p.name] != p.default

    def _construct_ctx(ctx):
        from .defaults import _create_default_ctx
        from .context import _Module, _Context

        if isinstance(ctx, _Module):
            _ctx = ctx.ctx
        elif isinstance(ctx, _Context):
            _ctx = ctx
        elif ctx is None:
            _ctx = _create_default_ctx()
        else:
            raise ValueError("Unknown ctx" + ctx)  # noqa
        return _ctx

    def _construct_datatype(dt_):
        from .classes import _Datatype

        if isinstance(dt_, _Datatype):
            return dt_
        elif isinstance(dt_, dict):
            return _ctx.def_datatype(dt_)
        else:
            return _ctx[dt_]

    def _not_default_params_with_validation(sig, ba):
        for param in sig.parameters.values():
            if _param_is_not_default(param, ba):
                if _param_is_not_empty(param):
                    dt_from_annotation = _construct_datatype(param.annotation)
                    if dt_from_annotation is not None:
                        yield param, dt_from_annotation
                elif param.name in kwargs:
                    dt_from_kwargs = _construct_datatype(kwargs[param.name])
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

    _ctx = _construct_ctx(ctx)
    return _decorator


def validate_args(fn=None, **kwargs):
    ctx = kwargs.pop('ctx', None)
    _decorator = validate_args_with_ctx(ctx=ctx, **kwargs)
    if fn is None:
        return _decorator
    else:
        return _decorator(fn)
