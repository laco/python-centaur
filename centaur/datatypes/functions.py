from .classes import _Context, _Module, _Datatype


def datatype_from_dict(d):
    return _Datatype.from_dict(d)


def module_from_dict(d):
    return _Module.from_dict(d)


def load_datatypes(module_list):
    return _Context(module_list=module_list)


def def_datatype(type_, **kwargs):
    return _Datatype(type_, **kwargs)


def fulfill(value, datatype, _throw_exception=True):
    return datatype.fulfill(value, _throw_exception=_throw_exception)
