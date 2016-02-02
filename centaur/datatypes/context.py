import yaml
from centaur.utils import without_items, IDGenerator
from .classes import StringDatatype, NumberDataType, IntegerDataType, DictDataType, \
    ListDatatype, NoneDatatype, ExtendedDataType, UnionDatatype, MaybeDatatype, \
    BooleanDataType
from .defaults import _create_default_ctx


class _Types(object):
    string = 'string'
    number = 'number'
    integer = 'integer'
    boolean = 'boolean'

    list = 'list'
    dict = 'dict'
    union = 'union'
    maybe = 'maybe'
    none = 'none'


PRIMITIVE_TYPES = [_Types.string, _Types.none, _Types.number, _Types.integer, _Types.boolean]
COMPOSITION_TYPES = [_Types.list, _Types.dict, _Types.union, _Types.maybe]


class YMLFileLoadMixin(object):
    @classmethod
    def from_file(cls, f):
        with open(f, 'r') as content_file:
            content = content_file.read()
        if f.endswith('yml'):
            return cls.from_yml(content)

    @classmethod
    def from_yml(cls, yml_content):
        d = yaml.load(yml_content)
        return cls.from_dict(d)


class _Context(YMLFileLoadMixin, object):
    def __init__(self):
        self._datatypes = {}
        self.linked_ctxs = {}
        self.id_generator = IDGenerator()
        self.error_templates = {}

    @classmethod
    def create_empty(cls):
        return cls()

    @classmethod
    def from_dict(cls, d):
        ctx = cls()
        return ctx.def_datatypes(d)

    def def_datatypes(self, dt_definitions):
        for k, v in dt_definitions.items():
            self.def_datatype(v, name=k)
        return self

    def def_datatype(self, dt_definition, name=None):
        name = name or self._gen_dt_name(dt_definition)
        type_ = dt_definition.get('type')
        type_cls_ = self.cls_for_type(type_)
        if type_ in PRIMITIVE_TYPES:
            options = without_items(dt_definition, ['type', 'name'])
        elif type_ == _Types.list:
            options = without_items(dt_definition, ['type', 'items', 'name'])
            if 'items' in dt_definition:
                options['items'] = self.def_datatype(dt_definition['items'])
        elif type_ == _Types.dict:
            options = without_items(dt_definition, ['type', 'fields', 'name'])
            if 'fields' in dt_definition:
                options['fields'] = {k: self.def_datatype(
                    dt_definition['fields'][k],
                    name="{}/{}".format(name, k)) for k, v in dt_definition['fields'].items()}
        elif type_ == _Types.union:
            options = without_items(dt_definition, ['type', 'types', 'name'])
            if 'types' in dt_definition:
                options['types'] = [self.def_datatype(d) for d in dt_definition['types']]
        elif type_ == _Types.maybe:
            options = without_items(dt_definition, ['type', 'base', 'name'])
            if 'base' in dt_definition:
                options['base'] = self.def_datatype(dt_definition['base'])

        else:
            # Keep all options for extended datatype
            options = without_items(dt_definition, [])

        datatype = type_cls_(_ctx=self, options=options, name=name)
        return self.add_datatype(name, datatype)

    def _gen_dt_name(self, dt_definition):
        return dt_definition['name'] if 'name' in dt_definition else \
            self.id_generator.generate_id(dt_definition.get('type'))

    def add_datatype(self, name, datatype):
        self._datatypes[name] = datatype
        return datatype

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
            else:  # noqa
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
            _Types.boolean: BooleanDataType,
        }
        try:
            return types_to_clss[type_]
        except KeyError:
            return ExtendedDataType


class _Module(YMLFileLoadMixin, object):
    def __init__(self, name, ns, ctx):
        self.name = name
        self.ns = ns
        self.ctx = ctx

    @classmethod
    def from_dict(cls, d):
        name = d.get('name')
        ns = d.get('ns', None)
        datatypes = d.get('datatypes')
        ctx = _Context.from_dict(datatypes)
        ctx.link_ctx(_create_default_ctx(), prefix='centaur')
        return cls(name=name, ns=ns, ctx=ctx)

    def items(self):
        return ((k, v) for k, v in self.ctx._datatypes.items())

    def __getitem__(self, key):
        return self.ctx.__getitem__(key)

    def get_datatype(self, name):
        return self.ctx.__getitem__(name)
