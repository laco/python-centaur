from centaur.funcprog import curry, lazy, compose


@curry
def sample_add(a, b):
    return a + b


@curry
def sample_multiply(a, b):
    return a * b


def test_curry_functions():
    add_1 = sample_add(1)
    add_2 = sample_add(2)
    add_b = sample_add(b=4)

    assert sample_add(1, 2) == 3
    assert add_1(1) == 2
    assert add_2(1) == 3
    assert add_b(1) == 5
    assert sample_add(1)(1) == 2


global_param = 0


def _side_effect(param):
    global global_param
    global_param = param


@lazy
def lazy_add(a, b):
    _side_effect(a + b)
    return a + b


def test_lazy_function_calls():
    c = lazy_add(1, 1)
    assert global_param == 0  #
    assert c == 2  # evaluation v. side_effect called
    assert global_param == 2


def test_fn_composition():
    double_plus_1 = compose(sample_add(1), sample_multiply(2))
    assert double_plus_1(2) == 5
    assert double_plus_1(0) == 1
    assert double_plus_1(-1) == -1

    double_neg_plus_1 = compose(sample_add(1), sample_multiply(-1), sample_multiply(2))

    assert double_neg_plus_1(10) == -19
    assert compose(sample_add(-1), sample_multiply)(2, 3) == 5
    assert compose()(1) == 1  # identity

    def factorial(n):
        return compose(*[sample_multiply(i) for i in range(1, n + 1)])(1)

    factorial_10 = 10 * 9 * 8 * 7 * 6 * 5 * 4 * 3 * 2
    assert factorial(10) == factorial_10
    assert factorial(2) == 2
    assert factorial(3) == 6
