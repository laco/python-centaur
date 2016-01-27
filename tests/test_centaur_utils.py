from centaur.utils import wraps_w_signature, call_in_ctx, select_params_for_fn
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
