from centaur.datatypes import def_datatype, fulfill, TypeMismatchError, \
    InvalidIntegerValue, InvalidDataTypeDefinition, InvalidValueError, ValidationError, \
    datatype_from_dict

import pytest

string_dt = def_datatype(type_="string")
number_dt = def_datatype(type_="number")
integer_dt = def_datatype(type_="integer")
url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


def test_invalid_datatype_definitions():
    with pytest.raises(InvalidDataTypeDefinition):
        def_datatype(type_="string", gt="invalid_value")


def test_list_relations():
    one_long_list = def_datatype(type_="list", length=1)
    zero_long_list = def_datatype(type_="list", length_min=0, length_max=0)

    assert fulfill([0], one_long_list)
    assert fulfill([[]], one_long_list)
    assert fulfill([], zero_long_list)

    for l in [[], [0, 1], [[], []]]:
        with pytest.raises(InvalidValueError):
            fulfill(l, one_long_list)
    for l in [[0, 1], [[], []], [[]]]:
        with pytest.raises(InvalidValueError):
            fulfill(l, zero_long_list)


def test_catch_exception_on_fulfill():
    sample2_dt = datatype_from_dict({'type': 'integer', 'lt': 100, 'gte': 0})
    result = fulfill(100, sample2_dt, _throw_exception=False)
    assert isinstance(result, Exception)
