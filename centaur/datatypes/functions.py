import re
from .commons import Types, Rels
from .classes import _Context, _Module, _Datatype

from .exceptions import InvalidValueError, TypeMismatchError, InvalidIntegerValue


def datatype_from_dict(d):
    return _Datatype.from_dict(d)


def module_from_dict(d):
    return _Module.from_dict(d)


def load_datatypes(module_list):
    return _Context(module_list=module_list)


def def_datatype(type_, **kwargs):
    return _Datatype(type_, **kwargs)


def fulfill(value, datatype, _throw_exception=True):
    def _fulfill_union(value, datatype):
        subtypes = datatype.params.get('types', [])
        results = [fulfill(value, st, _throw_exception=False) for st in subtypes]
        if not any([isinstance(r, bool) and r is True for r in results]):
            # TODO: merge union exceptions
            for e in results:
                if isinstance(e, (InvalidValueError)):
                    raise e
            for e in results:
                if isinstance(e, (TypeMismatchError)):
                    raise e
        else:
            return True

    def _fulfill_maybe(value, datatype):
        union_dt = _Datatype(type_=Types.UNION, types=[
            _Datatype(type_=Types.NONE),
            datatype.params.get('base')
        ])
        return _fulfill_union(value, union_dt)

    def _fulfill(value, datatype):
        if datatype.type_ == Types.UNION:
            return _fulfill_union(value, datatype)
        elif datatype.type_ == Types.MAYBE:
            return _fulfill_maybe(value, datatype)
        else:
            return _check_type(value, datatype) and _check_params(value, datatype)

    if _throw_exception is False:
        try:
            return _fulfill(value, datatype)
        except Exception as e:
            return e
    else:
        return _fulfill(value, datatype)


def _check_type(value, datatype, _throw_exception=True):
    def _check_integer(value):
        "returns True if the value is a whole number"
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            return True
        else:
            raise InvalidIntegerValue("{0} is not an integer.".format(value))

    type_ = datatype.type_
    if type_ == Types.STRING and isinstance(value, str):
        return True
    elif type_ in [Types.INTEGER, Types.NUMBER] and isinstance(value, (int, float)):
        return type_ == Types.NUMBER or (type_ == Types.INTEGER and _check_integer(value))
    elif type_ == Types.LIST and isinstance(value, (list, tuple)):
        return True
    elif type_ == Types.DICT and isinstance(value, dict):
        return True
    elif type_ == Types.NONE and value is None:
        return True
    else:
        if _throw_exception:
            raise TypeMismatchError("Invalid value for {0}: {1} (type mismatch).".format(type_, value))
        else:
            return False


def _check_params(value, datatype, _throw_exception=True):
    return all([_check_param(value, param, pvalue, _throw_exception) for param, pvalue in datatype.params.items()])


def _check_param(value, param, pvalue, _throw_exception=True):
    def _regex_fulfill(value, p):
        return re.match(p, value) is not None

    _param_check_fn_mapping = {
        Rels.GT: lambda value, p: value > p,
        Rels.LT: lambda value, p: value < p,
        Rels.LTE: lambda value, p: value <= p,
        Rels.GTE: lambda value, p: value >= p,
        Rels.NE: lambda value, p: value != p,
        Rels.EQ: lambda value, p: value == p,
        Rels.REGEX: _regex_fulfill
    }

    if param in _param_check_fn_mapping:
        ret = _param_check_fn_mapping[param](value, pvalue)
    elif param in [Rels.LENGTH, Rels.LENGTH_MAX, Rels.LENGTH_MIN]:
        length = len(value)
        if param == Rels.LENGTH:
            ret = _param_check_fn_mapping[Rels.EQ](length, pvalue)
        elif param == Rels.LENGTH_MAX:
            ret = _param_check_fn_mapping[Rels.LTE](length, pvalue)
        elif param == Rels.LENGTH_MIN:
            ret = _param_check_fn_mapping[Rels.GTE](length, pvalue)
    elif param == Rels.ITEMS:
        ret = all([fulfill(item, _Datatype.ensure_datatype(pvalue)) for item in value])
    elif param == Rels.FIELDS:
        ret = all([fulfill(value[fkey], _Datatype.ensure_datatype(fvalue)) for fkey, fvalue in pvalue.items()])
    else:
        ret = False
    if not ret and _throw_exception:
        raise InvalidValueError("Invalid value {0} for definition {1} {2}".format(value, param, pvalue))
    else:
        return ret
