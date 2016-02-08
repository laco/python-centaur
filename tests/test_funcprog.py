from centaur.funcprog import curry


@curry
def sample_add(a, b):
    return a + b


def test_curry_functions():
    add_1 = sample_add(1)
    add_2 = sample_add(2)
    add_b = sample_add(b=4)

    assert sample_add(1, 2) == 3
    assert add_1(1) == 2
    assert add_2(1) == 3
    assert add_b(1) == 5
