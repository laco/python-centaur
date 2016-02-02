from .context import _Context, _Module
from .decorators import validate_args, validate_args_with_ctx
from .exceptions import ValidationError
from .classes import _Datatype


def def_datatypes(dt_definitions, _ctx=None):
    ctx = _ctx or _Context.create_empty()
    return ctx.def_datatypes(dt_definitions)


def def_datatype(dt_definition, _ctx=None):
    ctx = _ctx or _Context.create_empty()
    dt = ctx.def_datatype(dt_definition)
    return dt


def load_module(module_def):
    if isinstance(module_def, dict):
        return _Module.from_dict(module_def)
    elif isinstance(module_def, str):
        return _Module.from_file(module_def)


def fulfill(value, datatype):
    return datatype.fulfill(value)


def guard(value, datatype):
    return datatype.guard(value)


__all__ = ['def_datatypes', 'def_datatype', 'load_module', 'fulfill', 'guard',
           '_Context', '_Module', '_Datatype',
           'validate_args', 'validate_args_with_ctx',
           'ValidationError',
           ]
