import pytest
from centaur.safe_import import safe_import, SafeImportError


def test_safe_import_missing_module():
    module = safe_import("module_name_for_inexistent_module")
    assert module is not None
    with pytest.raises(SafeImportError):
        module.missing_function()


def test_safe_import_ok_module():
    module = safe_import("os.path")
    exists = safe_import("os.path", "exists")
    assert module is not None
    assert module.exists(__file__) is True
    assert exists(__file__) is True


def test_safe_import_missing_module_with_message():
    module = safe_import("module_name_for_inexistent_module", msg="Plz. install this awesome package!")
    try:
        module.missing_function()
    except SafeImportError as e:
        assert str(e) == "Plz. install this awesome package!"


def test_safe_import_missing_just_few_objects():
    o1, o2 = safe_import('fakemodule_iguess', 'o1', 'o2')

    assert o1 is not None
    try:
        o1()
    except SafeImportError as e:
        assert str(e) == 'Missing fakemodule_iguess.o1'
