class DatatypeError(Exception):
    pass


class ValidationError(DatatypeError):
    pass


class InvalidDataTypeDefinition(DatatypeError):
    pass


class InvalidModuleDefinition(DatatypeError):
    pass


class TypeMismatchError(ValidationError):
    pass


class InvalidValueError(ValidationError):
    pass


class InvalidIntegerValue(ValidationError):
    pass
