class Types(object):
    NONE = "none"
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    LIST = "list"
    DICT = "dict"
    UNION = "union"
    MAYBE = "maybe"

    simple_datatypes = [NONE, STRING, INTEGER, NUMBER, LIST, DICT, UNION, MAYBE]


class Rels(object):
    EQ = 'eq'
    NE = 'ne'
    GT = 'gt'
    LT = 'lt'
    GTE = 'gte'
    LTE = 'lte'

    LENGTH = 'length'
    LENGTH_MIN = 'length_min'
    LENGTH_MAX = 'length_max'
    REGEX = 'regex'

    ITEMS = 'items'
    FIELDS = 'fields'

    TYPES = 'types'
    BASE = 'base'
