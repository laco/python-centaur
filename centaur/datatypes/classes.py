import re
from .commons import Types, Rels
from .exceptions import InvalidDataTypeDefinition, InvalidModuleDefinition, InvalidValueError, TypeMismatchError, InvalidIntegerValue


def _allowed_arguments_for(type_):
    if type_ in [Types.INTEGER, Types.NUMBER]:
        return [Rels.EQ, Rels.NE, Rels.GT, Rels.LT, Rels.GTE, Rels.LTE]
    elif type_ in [Types.STRING]:
        return [Rels.EQ, Rels.NE, Rels.LENGTH, Rels.LENGTH_MIN, Rels.LENGTH_MAX, Rels.REGEX]
    elif type_ in [Types.LIST]:
        return [Rels.LENGTH, Rels.LENGTH_MIN, Rels.LENGTH_MAX, Rels.ITEMS]
    elif type_ in [Types.DICT]:
        return [Rels.FIELDS]
    elif type_ in [Types.UNION]:
        return [Rels.TYPES]
    elif type_ in [Types.MAYBE]:
        return [Rels.BASE]


class _Datatype(object):

    def __init__(self, type_, **kwargs):
        def _check_kwargs(type_, kwargs):
            for k in kwargs:
                if k not in _allowed_arguments_for(type_):
                    raise InvalidDataTypeDefinition("Invalid argument {0} for datatype {1}".format(k, type_))
            return True

        _check_kwargs(type_, kwargs)

        self.type_ = type_
        self.params = kwargs

    def __repr__(self):
        return "Datatype(\"{type_}\", {params})".format(type_=self.type_, params=self.params)

    @classmethod
    def ensure_datatype(cls, dt):
        if isinstance(dt, _Datatype):
            return dt
        elif isinstance(dt, dict):
            return cls.from_dict(dt)
        else:
            raise InvalidDataTypeDefinition("Cannot create datatype from {0}".format(dt))

    @classmethod
    def from_dict(cls, d):
        d_ = {k: v for k, v in d.items() if k != 'type'}
        type_ = d['type']
        return cls(type_, **d_)

    def fulfill(self, value, _throw_exception=True):

        def _fulfill_union(value):
            subtypes = self.params.get('types', [])
            results = [st.fulfill(value, _throw_exception=False) for st in subtypes]
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

        def _fulfill_maybe(value):
            union_dt = _Datatype(type_=Types.UNION, types=[
                _Datatype(type_=Types.NONE),
                self.params.get('base')
            ])
            return union_dt.fulfill(value)

        def _fulfill(value):
            if self.type_ == Types.UNION:
                return _fulfill_union(value)
            elif self.type_ == Types.MAYBE:
                return _fulfill_maybe(value)
            else:
                return self._check_type(value) and self._check_params(value)

        if _throw_exception is False:
            try:
                return _fulfill(value)
            except Exception as e:
                return e
        else:
            return _fulfill(value)

    def _check_type(self, value, _throw_exception=True):
        def _check_integer(value):
            "returns True if the value is a whole number"
            if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
                return True
            else:
                raise InvalidIntegerValue("{0} is not an integer.".format(value))

        type_ = self.type_
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

    def _check_params(self, value,  _throw_exception=True):
        return all([self._check_param(value, param, pvalue, _throw_exception) for param, pvalue in self.params.items()])

    def _check_param(self, value, param, pvalue, _throw_exception=True):
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
            dt = _Datatype.ensure_datatype(pvalue)
            ret = all([dt.fulfill(item) for item in value])
        elif param == Rels.FIELDS:
            ret = all([_Datatype.ensure_datatype(fvalue).fulfill(value[fkey]) for fkey, fvalue in pvalue.items()])
        else:
            ret = False
        if not ret and _throw_exception:
            raise InvalidValueError("Invalid value {0} for definition {1} {2}".format(value, param, pvalue))
        else:
            return ret


class _Module(object):
    def __init__(self, name, datatypes=None):
        self.name = name
        self._datatypes = {} if datatypes is None else \
                          {name: _Datatype.ensure_datatype(dt) for name, dt in datatypes.items()}

    def get_datatype(self, datatype_name):
        return self._datatypes[datatype_name]

    def get_datatypes(self, datatype_names):
        return [self.get_datatype(dtn) for dtn in datatype_names or []]

    def as_ctx(self):
        return _Context(module_list=[self])

    @classmethod
    def ensure_module(cls, m):
        if isinstance(m, _Module):
            return m
        elif isinstance(m, dict):
            return cls.from_dict(m)
        else:
            raise InvalidModuleDefinition("Cannot instantiate module from {0}".format(m))

    @classmethod
    def from_dict(cls, d):
        name = d.get("name")
        datatypes = d.get("datatypes", None)
        m = cls(name=name, datatypes=datatypes)
        return m


class _Context(object):
    def __init__(self, module_list=None):
        self.modules = [_Module.ensure_module(m) for m in module_list or []]

    def _parse_datatype_name(self, datatype_name):
        n = datatype_name.split(":")
        if len(n) == 3:
            return n
        elif len(n) == 2:
            return None, n[0], n[1]
        elif len(n) == 1:
            return None, None, n[0]
        else:
            raise KeyError("Bad key for datatype: {0}".format(datatype_name))

    def _filter_modules(self, ns=None, mname=None):
        def _check_ns(module_, ns):
            return ns is None or ns == module_.ns

        def _check_mname(module_, mname):
            return mname is None or module_.name == mname

        return [
            m for m in self.modules
            if _check_ns(m, ns) and _check_mname(m, mname)
        ]

    def get_datatype(self, datatype_name):
        ns, mname, dname = self._parse_datatype_name(datatype_name)
        for m in self._filter_modules(ns, mname):
            try:
                return m.get_datatype(dname)
            except KeyError:
                continue
        raise KeyError("Datatype {0} not found in context.".format(datatype_name))

    def get_datatypes(self, datatype_names):
        return [self.get_datatype(dtn) for dtn in datatype_names or []]
