from centaur.datatypes import def_datatype, fulfill, TypeMismatchError, \
    InvalidValueError, module_from_dict, load_datatypes, default_ctx

import pytest


string_dt = def_datatype(type_="string")
number_dt = def_datatype(type_="number")
integer_dt = def_datatype(type_="integer")
url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


def test_module_from_dict():
    module_dict = {
        "name": "sample-module",
        "description": "Sample Module for Testing",
        "datatypes": {
            "sample1": {"type": "number", "gt": 0},
            "sample2": {"type": "string", "length_max": 255},
        }
    }
    m = module_from_dict(module_dict)
    # assert m.name == "sample-module"

    sample1_dt = m.get_datatype("sample1")
    assert fulfill(1, sample1_dt) is True
    s1_dt, s2_dt = m.get_datatypes(["sample1", "sample2"])

    assert s1_dt is not None and s2_dt is not None
    assert fulfill(1, s1_dt) and fulfill("aaa", s2_dt)


def test_load_extended_datatypes():
    module_dict = {
        "name": "sample-module",
        "description": "Sample module with extends",
        "datatypes": {
            "sample1": {"type": "dict", "fields": {
                "a": {"type": "string"},
                "b": {"type": "string"},
            }},
            "sample2": {"extends": "sample1",
                        "fields": {"c": {"type": "integer"}}},
        }}
    m = module_from_dict(module_dict)
    sample2 = m.get_datatype("sample2")
    assert fulfill({"a": "x", "b": "x", "c": 10}, sample2)


def test_load_datatypes():
    m1_dict = {
        "name": "sample1-module",
        "description": "Sample Module for Testing",
        "datatypes": {
            "sampleSame": {"type": "number", "gt": 0},
            "sample1": {"type": "string", "length_max": 128},
        }
    }
    m2_dict = {
        "name": "sample2-module",
        "description": "Sample Module for Testing",
        "datatypes": {
            "sampleSame": {"type": "integer", "gt": 1},
            "sample2": {"type": "list", "length_max": 256},
        }
    }
    ctx = load_datatypes([m1_dict, m2_dict])
    assert ctx.get_datatype("sample1").type_ == "string"
    assert ctx.get_datatype("sample2").type_ == "list"
    with pytest.raises(KeyError):
        ctx.get_datatype("sample3")

    ss1, ss2, ss3 = ctx.get_datatypes(["sample1-module:sampleSame", "sample2-module:sampleSame", "sampleSame"])
    assert ss1.type_ == "number"
    assert ss2.type_ == "integer"
    assert ss1 == ss3
    assert ss1 != ss2


def test_default_ctx():
    email_dt = default_ctx.get_datatype("email")
    assert fulfill("example.user+12@example.com", email_dt) is True
    with pytest.raises(InvalidValueError):
        fulfill("@example", email_dt)
