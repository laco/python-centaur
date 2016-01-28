import pytest
import os
import datetime
from centaur import datatypes as dt
from centaur.utils import select_items


url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
number_dt = dt.def_datatype({'type': 'number'})
integer_dt = dt.def_datatype({'type': 'integer'})
sample_service_yml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_service.yml")


def test_simple_datatype_definition():
    string_dt = dt.def_datatype({'type': 'string', 'length': 4, 'name': 'string_dt'})
    list_dt = dt.def_datatype({'type': 'list', 'length_min': 1, 'length_max': 2})
    none_dt = dt.def_datatype({'type': 'none'})

    # True
    assert dt.fulfill('xxxx', string_dt)
    assert dt.fulfill([1], list_dt)
    assert dt.fulfill([1, 2], list_dt)
    assert dt.fulfill(None, none_dt)
    assert dt.fulfill(1.12, number_dt)
    assert dt.fulfill(10.0, integer_dt)

    # False
    assert dt.fulfill('xxxxx', string_dt) is False
    assert dt.fulfill([1, 2, 3], list_dt) is False
    assert dt.fulfill([], list_dt) is False
    assert dt.fulfill(False, none_dt) is False
    assert dt.fulfill('113', number_dt) is False
    assert dt.fulfill(10.1, integer_dt) is False


def test_integer_datatype_respect_floats():
    assert dt.fulfill(1.0, integer_dt) is True
    assert dt.fulfill(1.0, number_dt) is True
    assert dt.fulfill(1.123, number_dt) is True

    with pytest.raises(dt.ValidationError):
        dt.guard(1.123, integer_dt) is False


def test_boolean_datatype():
    boolean_dt = dt.def_datatype({'type': 'boolean'})
    true_boolean_dt = dt.def_datatype({'type': 'boolean', 'eq': True})

    assert dt.fulfill(True, boolean_dt)
    assert not dt.fulfill(None, boolean_dt)

    assert dt.fulfill(True, true_boolean_dt)
    assert not dt.fulfill(False, true_boolean_dt)


def test_number_relations():
    greater_than_20 = dt.def_datatype({'type': 'number', 'gt': 20})
    less_than_20 = dt.def_datatype({'type': 'number', 'lt': 20})
    min_20_max_30 = dt.def_datatype({'type': 'number', 'gte': 20, 'lte': 30})
    not_equal_20 = dt.def_datatype({'type': 'number', 'ne': 20})
    equal_20 = dt.def_datatype({'type': 'number', 'eq': 20})

    assert dt.fulfill(21, greater_than_20) is True

    assert dt.fulfill(19, less_than_20) is True
    assert dt.fulfill(21, not_equal_20) is True
    assert dt.fulfill(20, equal_20) is True

    for i in range(20, 31):
        assert dt.fulfill(i, min_20_max_30)

    with pytest.raises(dt.ValidationError):
        dt.guard(20, greater_than_20)

    with pytest.raises(dt.ValidationError):
        dt.guard(20, less_than_20)

    with pytest.raises(dt.ValidationError):
        dt.guard(20, not_equal_20)

    with pytest.raises(dt.ValidationError):
        dt.guard(19, equal_20)


def test_dict_datatype_simple():
    dict_dt = dt.def_datatype({'type': "dict"})
    assert dt.fulfill({}, dict_dt)


def test_list_and_dict_composition_definition():
    user_dt = dt.def_datatype({
        'type': 'dict',
        'required': ['email', 'pw'],
        'fields': {
            'email': {'type': 'string', 'length_min': 10, 'contains': '@'},
            'pw': {'type': 'string', 'contains': '1', 'not_contains': '123', 'not_in': ['123456']},
            'tags': {'type': 'list', 'items': {'type': 'string', 'in': ['A', 'B', 'C']}}
        }})

    assert dt.fulfill({'email': 'test@example.com', 'pw': 'xxx321', 'tags': ['A']}, user_dt)
    assert not dt.fulfill({'pw': '123456', 'email': 'test@example.com'}, user_dt)
    assert not dt.fulfill({'pw': '321'}, user_dt)


def test_extended_datatype_definition():
    dts = dt.def_datatypes({
        'sample1': {'type': 'string', 'length_min': 1},
        'sample2': {'type': 'sample1', 'length_max': 1},
    })

    assert dt.fulfill('s', dts['sample2'])
    assert dt.fulfill(12, dts['sample2']) is False
    assert dt.fulfill('ss', dts['sample1'])
    assert dt.fulfill('ss', dts['sample2']) is False


def test_list_of_lists_validation():
    list_of_length2_gt100_number_lists = dt.def_datatype({
        'type': 'list',
        'items': {
            'type': 'list',
            'length': 2,
            'items': {
                'type': 'number',
                'gt': 100
                }}})
    assert dt.fulfill([[101, 102], [100.01, 100.02]], list_of_length2_gt100_number_lists)


def test_list_item_validation():
    integer_list = dt.def_datatype({'type': 'list', 'items': {'type': 'integer'}})
    lt100_integer_list = dt.def_datatype({
        'type': 'list',
        'items': {'type': 'integer', 'lt': 100}})

    assert dt.fulfill([0, 1, 2, 3], integer_list)
    assert dt.fulfill([], integer_list)
    assert not dt.fulfill(["a", "b", "c"], integer_list)

    assert dt.fulfill([97, 98, 99], lt100_integer_list)
    assert not dt.fulfill([99, 100, 101], lt100_integer_list)


def test_list_relations():
    one_long_list = dt.def_datatype({'type': 'list', 'length': 1})
    zero_long_list = dt.def_datatype({'type': 'list', 'length_min': 0, 'length_max': 0})

    assert dt.fulfill([0], one_long_list)
    assert dt.fulfill([[]], one_long_list)
    assert dt.fulfill([], zero_long_list)

    for l in [[], [0, 1], [[], []]]:
        with pytest.raises(dt.ValidationError):
            dt.guard(l, one_long_list)
    for l in [[0, 1], [[], []], [[]]]:
        with pytest.raises(dt.ValidationError):
            dt.guard(l, zero_long_list)


def test_string_regex():
    url_dt = dt.def_datatype({'type': 'string', 'regex': url_regex})
    assert dt.fulfill("https://example.com", url_dt)
    assert not dt.fulfill("ftp://example.com", url_dt)


def test_enums_and_contains():
    dts = dt.def_datatypes({
        'enum1': {'type': 'string', 'enum': ['A', 'B', 'C']},
        'enum2': {'type': 'number', 'enum': [0, 1.1, 1.2]},
        'enum3': {'type': 'string', 'in': ['AA', 'BB', 'CC'], 'contains': 'A'}
        })
    enum1, enum2, enum3 = select_items(dts, ['enum1', 'enum2', 'enum3'])
    assert dt.fulfill('A', enum1)
    assert dt.fulfill(1.2, enum2)
    assert dt.fulfill('AA', enum3)


def test_maybe_datatypes():
    maybe_url_dt = dt.def_datatype(
        {'type': 'maybe', 'base': {'type': 'string', 'regex': url_regex}})
    assert dt.fulfill(None, maybe_url_dt)
    assert dt.fulfill('http://example.com/', maybe_url_dt)
    assert not dt.fulfill('xxxsd jdfhgdfhg ', maybe_url_dt)


def test_union_datatypes_integer_or_string():
    union_dt = dt.def_datatype(
        {'type': 'union', 'types': [
            {'type': 'string', 'length_min': 3},
            {'type': 'integer', 'gt': 3}
        ]})
    assert dt.fulfill('string is ok', union_dt)
    assert dt.fulfill(12345, union_dt)
    assert dt.fulfill(4, union_dt)
    assert dt.fulfill('aaa', union_dt)

    assert not dt.fulfill(['list', 'is', 'not', 'ok'], union_dt)
    assert not dt.fulfill(3, union_dt)
    assert not dt.fulfill('aa', union_dt)


sample_module_def = {
    'name': 'sample',
    'description': 'Sample service definition',
    'datatypes': {
        'sampleID': {'type': 'string', 'length_min': 5},
        'sampleEmail': {'type': 'centaur:emailAddress'},
    },
    'interface': {
        'sample_action': {
            'description': 'Sample action with parameters',
            'request': {
                'method': 'GET',
                'url': '/sample/',
                'params': {'id': 'sampleID'}
            },
            'response': {
                'text': {'type': 'string'}
            }
        }
    }
}


def test_link_ctx():
    dts1 = dt.def_datatypes({
        'sample11': {'type': 'string', 'enum': ['ACB', 'BCA', 'ABC']},
        'sample12': {'type': 'sample11', 'contains': 'ABC'}})

    dts2 = dt.def_datatypes({
        'sample21': {'type': 'dts1:sample11', 'length_min': 1},
        'sample22': {'type': 'dts1:sample12', 'length_max': 3},
    })
    dts2.link_ctx(dts1, prefix='dts1')

    assert dt.fulfill('BCA', dts2['sample21'])
    assert dt.guard('ABC', dts2['sample22'])


def test_load_module():
    m = dt.load_module(sample_module_def)
    assert m['sampleID'] is not None

    assert dt.fulfill('mail@example.com', m['centaur:email'])
    assert dt.fulfill('https://example.com/', m['centaur:url'])
    assert dt.fulfill(str(datetime.date.today()), m['centaur:date'])
    # assert dt.fulfill(str(datetime.datetime.now()), m['centaur:datetime'])  # FIXME
    for m, d in m.items():
        assert m in ['sampleID', 'sampleEmail']
        assert isinstance(d, dt._Datatype)


def test_guard_throw_exception():
    user_dt = dt.def_datatype({
        'type': 'dict',
        'fields': {
            'email': {'type': 'string', 'length_min': 10},
            'pw': {'type': 'string'},
            'tags': {'type': 'list', 'items': {'type': 'string'}}
        }})

    assert dt.guard({'email': 'test@example.com', 'pw': '', 'tags': ['a']}, user_dt)
    with pytest.raises(dt.ValidationError):
        dt.guard({'email': 'xxxxx'}, user_dt)


def test_guard_with_custom_exception_template():
    book_dt = dt.def_datatype({
        'type': 'dict',
        'fields': {
            'author': {'type': 'string', 'length_min': 5, 'name': 'author'},
            'title': {'type': 'string'},
        }
        })
    book_dt._ctx.error_templates['length_min'] = 'The string is two small: {value}'
    assert dt.guard({'author': 'John Doe', 'title': 'The Great Title of the book'}, book_dt)
    try:
        assert dt.guard({'author': 'sm', 'title': 'The Great Title of the book'}, book_dt)
    except dt.ValidationError as e:
        assert str(e) == 'The string is two small: \'sm\''
