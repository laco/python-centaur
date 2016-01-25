import re
from copy import deepcopy


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


def def_datatypes(dt_definitions, _ctx=None):
    ctx = _ctx or _Context.create_empty()
    return ctx.def_datatypes(dt_definitions)


def def_datatype(dt_definition, _ctx=None):
    ctx = _ctx or _Context.create_empty()
    dt = ctx.def_datatype(dt_definition)
    return dt


def fulfill(value, datatype):
    return datatype.fulfill(value)


class _Datatype(object):
    def __init__(self, options, _ctx):
        self._options = options
        self._ctx = _ctx

    def get_options(self):
        return self._options

    def validate_type(self, value):
        return True

    def fulfill(self, value, options=None):
        def _validate_option(value, option, opt):
            validate_fn = getattr(self, 'validate_{}'.format(option))
            return validate_fn(value, opt)
        options = options or self.get_options()
        return self.validate_type(value) and all([_validate_option(value, option, options[option]) for option in options])


class LengthValidationMixin(object):
    def validate_length(self, value, opt):
        return len(value) == opt

    def validate_length_min(self, value, opt):
        return len(value) >= opt

    def validate_length_max(self, value, opt):
        return len(value) <= opt


class EnumValidationMixin(object):
    def validate_enum(self, value, opt):
        return value in opt

    def validate_in(self, value, opt):
        return value in opt

    def validate_not_in(self, value, opt):
        return value not in opt


class ContainsValidationMixin(object):
    def validate_contains(self, value, opt):
        return opt in value

    def validate_not_contains(self, value, opt):
        return opt not in value


class ItemsValidationMixin(object):
    def validate_items(self, value, opt):
        item_dt = opt
        return all([fulfill(item, item_dt) for item in value])


class FieldsValidationMixin(object):
    def validate_fields(self, value, opt):
        def _validate_key(key, value):
            key_dt = opt[key]
            return fulfill(value.get(key), key_dt)
        return all([_validate_key(key, value) for key in value])

    def validate_required(self, value, opt):
        for key in opt:
            if key not in value:
                return False
        return True


class SortableValidationMixin(object):
    def validate_lt(self, value, opt):
        return value < opt

    def validate_gt(self, value, opt):
        return value > opt

    def validate_lte(self, value, opt):
        return value <= opt

    def validate_gte(self, value, opt):
        return value >= opt


class EqualityValidationMixin(object):

    def validate_eq(self, value, opt):
        return value == opt

    def validate_ne(self, value, opt):
        return value != opt


class RegexValidationMixin(object):
    def validate_regex(self, value, opt):
        return re.match(opt, value) is not None


class NoneDatatype(_Datatype):
    def validate_type(self, value):
        return value is None


class StringDatatype(EnumValidationMixin, ContainsValidationMixin, LengthValidationMixin, EqualityValidationMixin, RegexValidationMixin, _Datatype):
    def validate_type(self, value):
        return isinstance(value, str)


class NumberDataType(EnumValidationMixin, SortableValidationMixin, EqualityValidationMixin, _Datatype):
    def validate_type(self, value):
        return isinstance(value, (int, float))


class IntegerDataType(EnumValidationMixin, SortableValidationMixin, EqualityValidationMixin, _Datatype):
    def validate_type(self, value):
        return isinstance(value, int) or (isinstance(value, float) and value.is_integer())


class ListDatatype(ItemsValidationMixin, ContainsValidationMixin, LengthValidationMixin, _Datatype):
    def validate_type(self, value):
        return isinstance(value, list)


class DictDataType(FieldsValidationMixin, LengthValidationMixin, _Datatype):
    def validate_type(self, value):
        return isinstance(value, dict)


class ExtendedDataType(_Datatype):
    def fulfill(self, value, options=None):
        base_dt = self._ctx[self._options['type']]
        return base_dt.fulfill(value, options=without_items(options or self.get_options(), ['type']))

    def get_options(self):
        base_dt = self._ctx[self._options['type']]
        return deep_merge(base_dt.get_options(), self._options)


class UnionDatatype(_Datatype):
    def validate_types(self, value, opt):
        for t in opt:
            if t.fulfill(value):
                return True
        return False


class MaybeDatatype(_Datatype):
    def validate_base(self, value, opt):
        return value is None or opt.fulfill(value)


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


def without_items(dict_, keys):
    return {k: v for k, v in dict_.items() if k not in keys}


def with_items(dict_, keys):
    return {k: v for k, v in dict_.items() if k in keys}


def select_items(dict_, keys):
    return [dict_[k] for k in keys]


def deep_merge(d1, d2):
    ret = deepcopy(d1)
    for k, v in d2.items():
        if k in ret and isinstance(ret[k], dict):
            ret[k] = deep_merge(ret[k], v)
        else:
            ret[k] = deepcopy(v)
    return ret
