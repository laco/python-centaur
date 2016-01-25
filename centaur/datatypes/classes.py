from .mixins import EnumValidationMixin, ContainsValidationMixin, LengthValidationMixin,\
    EqualityValidationMixin, RegexValidationMixin, SortableValidationMixin, ItemsValidationMixin,\
    FieldsValidationMixin
from .utils import without_items, deep_merge


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
