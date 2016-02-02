from centaur.version import __version__ as v


def test_version_is_not_none():
    assert v is not None
