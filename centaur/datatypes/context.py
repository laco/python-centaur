from .utils import without_items
from .classes import StringDatatype, NumberDataType, IntegerDataType, DictDataType, \
    ListDatatype, NoneDatatype, ExtendedDataType, UnionDatatype, MaybeDatatype


class _Types(object):
    string = 'string'
    number = 'number'
    integer = 'integer'

    list = 'list'
    dict = 'dict'
    union = 'union'
    maybe = 'maybe'
    none = 'none'


PRIMITIVE_TYPES = [_Types.string, _Types.none, _Types.number, _Types.integer]
COMPOSITION_TYPES = [_Types.list, _Types.dict, _Types.union, _Types.maybe]


class _Context(object):
    def __init__(self):
        self._datatypes = {}
        self.linked_ctxs = {}

    @classmethod
    def create_empty(cls):
        return cls()

    def def_datatypes(self, dt_definitions):
        for k, v in dt_definitions.items():
            self.def_datatype(v, name=k)
        return self

    def def_datatype(self, dt_definition, name=None):
        type_ = dt_definition.get('type')
        type_cls_ = self.cls_for_type(type_)
        if type_ in PRIMITIVE_TYPES:
            options = without_items(dt_definition, ['type'])
        elif type_ == _Types.list:
            options = without_items(dt_definition, ['type', 'items'])
            if 'items' in dt_definition:
                options['items'] = self.def_datatype(dt_definition['items'])
        elif type_ == _Types.dict:
            options = without_items(dt_definition, ['type', 'fields'])
            if 'fields' in dt_definition:
                options['fields'] = {k: self.def_datatype(dt_definition['fields'][k]) for k, v in dt_definition['fields'].items()}

        elif type_ == _Types.union:
            options = without_items(dt_definition, ['type', 'types'])
            if 'types' in dt_definition:
                options['types'] = [self.def_datatype(d) for d in dt_definition['types']]
        elif type_ == _Types.maybe:
            options = without_items(dt_definition, ['type', 'base'])
            if 'base' in dt_definition:
                options['base'] = self.def_datatype(dt_definition['base'])

        else:
            # Keep all options for extended datatype
            options = without_items(dt_definition, [])

        datatype = type_cls_(_ctx=self, options=options)
        if name is not None:
            self.add_datatype(name, datatype)
        return datatype

    def add_datatype(self, name, datatype):
        self._datatypes[name] = datatype

    def def_extended_datatype(self, dt_definition, name=None):
        type_ = dt_definition.get('type')
        if type_ in self._datatypes:
            return

    def link_ctx(self, ctx, prefix):
        self.linked_ctxs[prefix] = ctx
        return self

    def items(self):
        return ((k, v) for k, v in self._datatypes.items())

    def __getitem__(self, key):
        splitted_key = key.rsplit(':', 1)
        if len(splitted_key) == 1:
            return self._datatypes[key]
        elif len(splitted_key) == 2:
            if splitted_key[0] in self.linked_ctxs:
                return self.linked_ctxs[splitted_key[0]][splitted_key[1]]
            else:
                raise ValueError("Unknown prefix: {} for datatype {}".format(*splitted_key))

    def cls_for_type(self, type_):
        types_to_clss = {
            _Types.string: StringDatatype,
            _Types.list: ListDatatype,
            _Types.dict: DictDataType,
            _Types.none: NoneDatatype,
            _Types.number: NumberDataType,
            _Types.integer: IntegerDataType,
            _Types.union: UnionDatatype,
            _Types.maybe: MaybeDatatype,
        }
        try:
            return types_to_clss[type_]
        except KeyError:
            return ExtendedDataType


class _Module(object):
    def __init__(self, name, ns, ctx):
        self.name = name
        self.ns = ns
        self.ctx = ctx

    @classmethod
    def from_dict(cls, d):
        name = d.get('name')
        ns = d.get('ns', None)
        datatypes = d.get('datatypes')
        ctx = _Context.create_empty()
        ctx = ctx.def_datatypes(datatypes)
        return cls(name=name, ns=ns, ctx=ctx)

    def items(self):
        return ((k, v) for k, v in self.ctx._datatypes.items())

    def __getitem__(self, key):
        return self.ctx.__getitem__(key)

    def get_datatype(self, name):
        return self.ctx.__getitem__(name)
