from .context import _Context, _Module
from .utils import select_items, with_items, without_items
from .decorators import validate_before_call
from .exceptions import ValidationError


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


def fulfill(value, datatype):
    return datatype.fulfill(value)


__all__ = ['def_datatypes', 'def_datatype', 'load_module', 'fulfill',
           'select_items', 'with_items', 'without_items',
           '_Context', '_Module',
           'validate_before_call',
           'ValidationError',
           ]
