from .defaults import _create_default_ctx


def datatype_from_dict(d, ctx_=None):
    ctx = ctx_ or _create_default_ctx()

    return ctx.datatype_from_dict(d)


def module_from_dict(d, ctx_=None):
    ctx = ctx_ or _create_default_ctx()
    return ctx.module_from_dict(d)


def load_datatypes(module_list, ctx_=None):
    ctx = ctx_ or _create_default_ctx()
    return ctx.load_datatypes(module_list)


def def_datatype(type_=None, extends_=None, ctx_=None, **kwargs):
    ctx = ctx_ or _create_default_ctx()
    return ctx.def_datatype(type_, extends_, **kwargs)
    # return _Datatype(type_, **kwargs)


def fulfill(value, datatype, _throw_exception=True):
    return datatype.fulfill(value, _throw_exception=_throw_exception)
