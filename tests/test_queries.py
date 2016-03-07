import pytest
from centaur.queries import parse_wt


@pytest.mark.parametrize(
    'w, value, result', [
        (('eq', 'name', 'Sample'), {'name': 'Sample'}, True),
        (('eq', 'name', 'Sample'), {'name': 'NOOOOO'}, False),

        (('neq', 'name', 'Sample'), {'name': 'NOOOO'}, True),
        (('neq', 'name', 'Sample'), {'name': 'Sample'}, False),

        (('lt', 'age', 10), {'age': 9}, True),
        (('lt', 'age', 10), {'age': 10}, False),

        (('gt', 'age', 10), {'age': 11}, True),
        (('gt', 'age', 10), {'age': 10}, False),

        (('lte', 'age', 10), {'age': 9}, True),
        (('lte', 'age', 10), {'age': 10}, True),
        (('lte', 'age', 10), {'age': 11}, False),

        (('gte', 'age', 10), {'age': 11}, True),
        (('gte', 'age', 10), {'age': 10}, True),
        (('gte', 'age', 10), {'age': 9}, False),

        (('in', 'category', ['A', 'B']), {'category': 'A'}, True),
        (('in', 'category', ['A', 'B']), {'category': 'B'}, True),
        (('in', 'category', ['A', 'B']), {'category': 'C'}, False),

        (('nin', 'category', ['A', 'B']), {'category': 'A'}, False),
        (('nin', 'category', ['A', 'B']), {'category': 'B'}, False),
        (('nin', 'category', ['A', 'B']), {'category': 'C'}, True),

        (('contains', 'tags', 'A'), {'tags': ['A', 'B']}, True),
        (('contains', 'tags', 'B'), {'tags': ['A', 'B']}, True),
        (('contains', 'tags', 'C'), {'tags': ['A', 'B']}, False),

        (('ncontains', 'tags', 'A'), {'tags': ['A', 'B']}, False),
        (('ncontains', 'tags', 'B'), {'tags': ['A', 'B']}, False),
        (('ncontains', 'tags', 'C'), {'tags': ['A', 'B']}, True),

        (('startswith', 'name', 'Example'), {'name': 'Example Name'}, True),
        (('startswith', 'name', 'Example'), {'name': 'Not-Example Name'}, False),

        (('endswith', 'name', 'Example'), {'name': 'First Example'}, True),
        (('endswith', 'name', 'Example'), {'name': 'Second Example End'}, False),

        (('is', 'required', True), {'required': False}, False),
        (('is', 'required', True), {'required': 1}, False),
        (('is', 'required', True), {'required': 'True'}, False),
        (('is', 'required', True), {'required': True}, True),

    ])
def test_parse_wt_simple(w, value, result):
    wq = parse_wt(w)
    assert wq.check(value) is result


def test_parse_wt_and_query():
    w = ('and',
         ('eq', 'name', 'Sample'),
         ('eq', 'age', 18))
    wq = parse_wt(w)
    assert wq.check({}) is False
    assert wq.check({'name': 'XXX', 'age': 18}) is False
    assert wq.check({'name': 'Sample', 'age': 17}) is False
    assert wq.check({'name': 'Sample', 'age': 18}) is True


def test_parse_wt_not():
    w = ('not',
         ('eq', 'name', 'Sample'))
    wq = parse_wt(w)
    assert wq.check({'name': 'Sample'}) is False
    assert wq.check({'name': 'Not Sample'}) is True


def test_parse_wt_or():
    w = ('or',
         ('eq', 'title', 'Example'),
         ('gt', 'length', 100))
    wq = parse_wt(w)
    assert wq.check({'title': 'Example'}) is True
    assert wq.check({'length': 101}) is True
    assert wq.check({'title': 'Not Example', 'length': 0}) is False


def test_query_repr():
    w = ('and',
         ('or',
          ('eq', 'name', 'Example1'),
          ('eq', 'name', 'Example2')),
         ('gt', 'age', 18))
    wq = parse_wt(w)
    assert repr(wq) == """
('and',
 ('or',
  ('eq', 'name', 'Example1'),
  ('eq', 'name', 'Example2')),
 ('gt', 'age', 18))
""".strip()


def test_empty_query():
    wq = parse_wt(None)
    assert wq.check({'anything': 'is ok'}) is True
    assert wq.check({}) is True

    assert repr(wq) == 'None'


def test_as_predicate():
    predicate = parse_wt(
        ('and',
         ('gt', 'value', 10),
         ('lte', 'value', 20))).as_predicate()

    assert predicate({'value': 20}) is True


def test_parse_wt_raise_exception_on_invalid_keyword():
    with pytest.raises(TypeError):
        parse_wt(('invalidke', 'Aaa', 'bbb'))


def test_parse_wt_raise_exception_on_missing_arguments():
    with pytest.raises(TypeError):
        parse_wt(('eq',))
