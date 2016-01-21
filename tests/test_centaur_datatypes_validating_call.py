from centaur.datatypes import ValidationError, validate_before_call, load_datatypes


import pytest
url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


def test_validate_before_call_w_datatypes_as_strings():
    ctx = load_datatypes([{
        "name": "sample",
        "description": "Sample Module for Testing",
        "datatypes": {
            "url": {"type": "string", "regex": url_regex},
            "positive": {"type": "number", "gt": 0},
        }}])

    @validate_before_call(ctx)
    def _test_fn(url: "sample:url", no_annotation,  param_w_default: 'positive'=None):
        return "valid url:{0}".format(url)

    assert _test_fn("http://example.com", None) == "valid url:http://example.com"
    with pytest.raises(ValidationError):
        _test_fn("s,djkdjfkdjsdkjfksdjf", None)
    with pytest.raises(ValidationError):
        _test_fn("http://example.com", None,  param_w_default=-1)


def test_validate_before_call_w_datatypes_as_dt():
    ctx = load_datatypes([{
        "name": "sample",
        "description": "Sample Module for Testing",
        "datatypes": {
            "url": {"type": "string", "regex": url_regex},
            "positive": {"type": "number", "gt": 0},
        }}])

    url_dt, positive_dt = ctx.get_datatypes(["url", "positive"])

    @validate_before_call
    def _test_fn(url: url_dt, no_annotation,  param_w_default: positive_dt=None):
        return "valid url:{0}".format(url)

    assert _test_fn("http://example.com", None) == "valid url:http://example.com"
    with pytest.raises(ValidationError):
        _test_fn("s,djkdjfkdjsdkjfksdjf", None)
    with pytest.raises(ValidationError):
        _test_fn("http://example.com", None,  param_w_default=-1)


def test_validate_before_call_w_bad_datatype_name():
    @validate_before_call
    def _test_fn(email: "email2"):
        return "valid email:{0}".format(email)

    with pytest.raises(KeyError):
        _test_fn("goodemail@example.com")
