from centaur.utils import wraps_w_signature, call_in_ctx, select_params_for_fn, without_items, with_items, deep_merge, IDGenerator, fill_defaults
from inspect import signature, Signature, Parameter


class Sample:
    __signature__ = Signature(parameters=[Parameter('test', Parameter.POSITIONAL_OR_KEYWORD)])


def sample_fn(a, b, c=None):
    return a, b, c


def wraps_w_signature_sample_decorator(fn):
    @wraps_w_signature(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper


def test_wraps_w_signature_keeps_signature():
    sample_decorated_fn = wraps_w_signature_sample_decorator(sample_fn)
    assert sample_decorated_fn.__signature__ == signature(sample_fn)


def test_call_function_from_ctx():
    sample_ctx = {
        'a': 10,
        'b': 20,
        'c': 30,
        'd': 40,
    }
    assert select_params_for_fn(sample_ctx, sample_fn) == {'a': 10, 'b': 20, 'c': 30}
    assert call_in_ctx(sample_ctx, sample_fn) == (10, 20, 30)


def test_without_items_fn():
    a = {'a': 'a', 'b': 'b', 'c': 'c'}
    assert without_items(a, ['a']) == {'b': 'b', 'c': 'c'}
    assert without_items(a, ['a', 'b']) == {'c': 'c'}


def test_select_items_fn():
    a = {'a': 'a', 'b': 'b', 'c': 'c'}
    assert with_items(a, ['a']) == {'a': 'a'}
    assert with_items(a, ['a', 'b']) == {'a': 'a', 'b': 'b'}


def test_deep_merge():
    a = {'a': 'a', 'b': 'b', 'c': {'D': 'D'}}
    b = {'a': 'a', 'b': 'b', 'c': {'E': 'E'}}

    m = deep_merge(a, b)
    assert m['c'] == {'D': 'D', 'E': 'E'}


def test_id_generator():
    g = IDGenerator()
    assert g.generate_id('sample') == 'sample0'
    assert g.generate_id('sample') == 'sample1'


def test_fill_defaults():
    data = {'a': 1, 'b': 2, 'c': None}
    data_defaults = {'b': 0, 'c': 3, 'd': -1}

    assert fill_defaults(data, data_defaults) == {'a': 1, 'b': 2, 'c': 3, 'd': -1}
    assert fill_defaults(data, data_defaults, keep_nones=True) == {'a': 1, 'b': 2, 'c': None, 'd': -1}
