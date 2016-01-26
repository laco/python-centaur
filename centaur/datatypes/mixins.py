import re


class LengthValidationMixin(object):
    msg_length = "{value} length is not {option_value}"
    msg_length_min = "{value} length is not at least {option_value}"
    msg_length_max = "{value} length is greater then {option_value}"

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
        return all([item_dt.guard(item) for item in value])


class FieldsValidationMixin(object):
    def validate_fields(self, value, opt):
        def _validate_key(key, value):
            key_dt = opt[key]
            return key_dt.guard(value.get(key))
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
