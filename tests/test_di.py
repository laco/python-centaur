from centaur.di import depends_on


@depends_on('a', 'b', 'c')
class A(object):
    pass


class B(object):
    pass


def test_simple_di_depends_on():
    bobj = B()
    aobj = A(a=10, b=bobj, c='Foo')

    # dependencies addedd to the object
    assert aobj.a == 10
    assert isinstance(aobj.b, B)
    assert aobj.c == 'Foo'

    # original classes are not modified
    assert aobj.__class__.__name__ == 'AWithDependenciesABC'
    assert aobj.__class__.__bases__[0].__name__ == 'DependsOnABCMixin'
    assert aobj.__class__.__bases__[1].__name__ == 'A'
