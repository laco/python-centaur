from centaur.datatypes import def_datatype, fulfill, TypeMismatchError, \
    InvalidIntegerValue, InvalidDataTypeDefinition, InvalidValueError, ValidationError, \
    datatype_from_dict

import pytest


string_dt = def_datatype(type_="string")
number_dt = def_datatype(type_="number")
integer_dt = def_datatype(type_="integer")


def test_invalid_datatype_definitions():
    with pytest.raises(InvalidDataTypeDefinition):
        def_datatype(type_="string", gt="invalid_value")


def test_simple_datatype():
    sample_dt = def_datatype(type_="string")
    assert sample_dt is not None
    assert sample_dt.type_ == "string"
    assert str(sample_dt) is not None


def test_simple_string_fulfill():
    sample_dt = def_datatype(type_="string")
    assert fulfill("sample string", sample_dt) is True


def test_simple_integer_fulfill():
    assert fulfill(123, integer_dt) is True


def test_simple_bad_datatype_shoud_raise_exception():
    with pytest.raises(TypeMismatchError):
        fulfill(1000, string_dt)

    with pytest.raises(TypeMismatchError):
        fulfill(1.234, string_dt)

    with pytest.raises(TypeMismatchError):
        fulfill("sdfsdf", integer_dt)


def test_integer_datatype_respect_floats():
    assert fulfill(1.0, integer_dt) is True
    assert fulfill(1.0, number_dt) is True
    assert fulfill(1.123, number_dt) is True

    with pytest.raises(InvalidIntegerValue):
        fulfill(1.123, integer_dt) is False


def test_number_relations():
    greater_than_20 = def_datatype(type_="number", gt=20)
    less_than_20 = def_datatype(type_="number", lt=20)
    min_20_max_30 = def_datatype(type_="number", gte=20, lte=30)
    not_equal_20 = def_datatype(type_="number", ne=20)
    equal_20 = def_datatype(type_="number", eq=20)

    assert fulfill(21, greater_than_20) is True

    assert fulfill(19, less_than_20) is True
    assert fulfill(21, not_equal_20) is True
    assert fulfill(20, equal_20) is True

    for i in range(20, 31):
        assert fulfill(i, min_20_max_30)

    with pytest.raises(InvalidValueError):
        fulfill(20, greater_than_20)

    with pytest.raises(InvalidValueError):
        fulfill(20, less_than_20)

    with pytest.raises(InvalidValueError):
        fulfill(20, not_equal_20)

    with pytest.raises(InvalidValueError):
        fulfill(19, equal_20)


def test_string_length():
    between_20_and_30_long_string = def_datatype(type_="string", length_min=20, length_max=30)
    string_20 = def_datatype(type_="string", length=20)

    for i in range(20, 31):
        assert fulfill("a" * i, between_20_and_30_long_string)

    for i in [19, 31]:
        with pytest.raises(InvalidValueError):
            fulfill("a" * i, between_20_and_30_long_string)

    assert fulfill("a" * 20, string_20)
    with pytest.raises(InvalidValueError):
        fulfill("a" * 19, string_20)


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


def test_datatype_from_dict():
    sample_dt = datatype_from_dict({'type': 'string'})
    sample2_dt = datatype_from_dict({'type': 'integer', 'lt': 100, 'gte': 0})
    assert sample_dt is not None
    assert sample_dt.type_ == 'string'
    assert sample2_dt is not None
    assert sample2_dt.type_ == 'integer'

    assert fulfill('1234', sample_dt)
    assert fulfill(0, sample2_dt) and fulfill(99, sample2_dt)


def test_catch_exception_on_fulfill():
    sample2_dt = datatype_from_dict({'type': 'integer', 'lt': 100, 'gte': 0})
    result = fulfill(100, sample2_dt, _catch_exceptions=True)
    assert isinstance(result, Exception)


def test_list_item_validation():
    integer_list = def_datatype(type_="list", items=def_datatype(type_="integer"))
    lt100_integer_list = datatype_from_dict({
        'type': 'list',
        'items': {'type': 'integer', 'lt': 100}})

    assert fulfill([0, 1, 2, 3], integer_list)
    assert fulfill([], integer_list)
    with pytest.raises(TypeMismatchError):
        fulfill(["a", "b", "c"], integer_list)

    assert fulfill([97, 98, 99], lt100_integer_list)
    with pytest.raises(InvalidValueError):
        fulfill([99, 100, 101], lt100_integer_list)


def test_list_of_lists_validation():
    list_of_length2_gt100_number_lists = datatype_from_dict({
        'type': 'list',
        'items': {
            'type': 'list',
            'length': 2,
            'items': {
                'type': 'number',
                'gt': 100
                }}})
    assert fulfill([[101, 102], [100.01, 100.02]], list_of_length2_gt100_number_lists)


def test_dict_datatype_simple():
    dict_dt = def_datatype(type_="dict")
    assert fulfill({}, dict_dt)


def test_dict_datatype_with_fields():
    dict_dt = datatype_from_dict({
        'type': 'dict',
        'fields': {
            'id': def_datatype(type_='integer', gt=0),
            'name': {'type': 'string', 'length_min': 3, 'length_max': 128}
        }})
    sample_data = {
        'id': 1,
        'name': 'ASD'
    }
    bad_sample_datas = [
        {'id': 'bad_id', 'name': 'ASD'},
        {'id': 0, 'name': 'ASD'},
        {'id': 1, 'name': 'aa'},
        {'id': 2, 'name': 'a'*129},
        {'id': 3, 'name': 0}

    ]
    assert fulfill(sample_data, dict_dt)
    for bad_sample in bad_sample_datas:
        with pytest.raises(ValidationError):
            fulfill(bad_sample, dict_dt)
