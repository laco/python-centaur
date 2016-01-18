from .commons import Types, Rels
from .exceptions import InvalidDataTypeDefinition, InvalidModuleDefinition


def _allowed_arguments_for(type_):
    if type_ in [Types.INTEGER, Types.NUMBER]:
        return [Rels.EQ, Rels.NE, Rels.GT, Rels.LT, Rels.GTE, Rels.LTE]
    elif type_ in [Types.STRING]:
        return [Rels.EQ, Rels.NE, Rels.LENGTH, Rels.LENGTH_MIN, Rels.LENGTH_MAX, Rels.REGEX]
    elif type_ in [Types.LIST]:
        return [Rels.LENGTH, Rels.LENGTH_MIN, Rels.LENGTH_MAX, Rels.ITEMS]
    elif type_ in [Types.DICT]:
        return [Rels.FIELDS]


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


class _Module(object):
    def __init__(self, name, datatypes=None):
        self.name = name
        self._datatypes = {} if datatypes is None else \
                          {name: _Datatype.ensure_datatype(dt) for name, dt in datatypes.items()}

    def get_datatype(self, datatype_name):
        return self._datatypes[datatype_name]

    def get_datatypes(self, datatype_names):
        return [self.get_datatype(dtn) for dtn in datatype_names or []]

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
