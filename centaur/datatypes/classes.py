from .mixins import EnumValidationMixin, ContainsValidationMixin, LengthValidationMixin,\
    EqualityValidationMixin, RegexValidationMixin, SortableValidationMixin, ItemsValidationMixin,\
    FieldsValidationMixin
from centaur.utils import without_items, deep_merge
from .exceptions import ValidationError


class _Datatype(object):
    def __init__(self, options, _ctx, name):
        self._options = options
        self._ctx = _ctx
        self.name = name

    def get_options(self):
        return self._options

    def validate_type(self, value):
        return True

    def get_exception_msg(self, option_name, option_value, value):
        if option_name in self._ctx.error_templates:
            template = self._ctx.error_templates[option_name]
        elif hasattr(self, 'msg_' + option_name):
            template = getattr(self, 'msg_' + option_name)
        else:
            template = "Value {value} is invalid for {datatype_name}. (Reason: {option_name} {option_value})"
        return template.format(**{
            'datatype_name': self.name,
            'option_name': option_name,
            'option_value': option_value,
            'value': repr(value)})

    def fulfill(self, value, options=None):
        try:
            return self.guard(value, options=options)
        except ValidationError:
            return False

    def guard(self, value, options=None):
        def _validate_option(value, option, opt):
            validate_fn = getattr(self, 'validate_{}'.format(option))
            if validate_fn(value, opt):
                return True
            else:
                raise ValidationError(self.get_exception_msg(option_name=option, option_value=opt, value=value))
        options = options or self.get_options()
        if self.validate_type(value):
            return all([_validate_option(value, option, options[option]) for option in options])
        else:
            raise ValidationError("Invalid type for {}. Value: {}".format(self.__class__.__name__, repr(value)))


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
        return (isinstance(value, int)) or (isinstance(value, float) and value.is_integer())


class BooleanDataType(EqualityValidationMixin, _Datatype):
    def validate_type(self, value):
        return isinstance(value, bool)


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

    def guard(self, value, options=None):
        base_dt = self._ctx[self._options['type']]
        return base_dt.guard(value, options=without_items(options or self.get_options(), ['type']))

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
