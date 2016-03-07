import operator
import logging

logger = logging.getLogger(__name__)


class WQuery(object):
    def check(self, value):  # noqa
        return False

    def as_predicate(self):
        return self.check


class PrimitiveWQuery(WQuery):
    def __init__(self, selector, argument):
        self.selector = selector
        self.argument = argument

    def select(self, value):
        return value.get(self.selector)

    def check(self, value):
        try:
            return self._operator(self.select(value), self.argument)
        except TypeError as e:
            logger.warn(e)
            return False

    def __repr__(self):
        return "('{}', '{}', {})".format(self._tag, self.selector, repr(self.argument))

    def to_list(self):
        return [self._tag, self.selector, self.argument]

    def __eq__(self, other):
        return all([
            self._tag == other._tag,
            self.selector == other.selector,
            self.argument == other.argument])


class CompositeWQuery(WQuery):
    def __init__(self, *subqueries):
        self.subqueries = subqueries

    def __repr__(self):
        def _space_indent(spaces, s):
            return '\n'. join([(' ' * spaces) + line for line in s.split('\n')])

        return "('{}',\n{})".format(
            self._tag,
            _space_indent(1,
                          ',\n'.join([repr(s) for s in self.subqueries])))

    def to_list(self):
        return [self._tag] + [s.to_list() for s in self.subqueries]

    def __eq__(self, other):
        return self._tag == other._tag and \
            len(self.subqueries) == len(other.subqueries) and \
            all([s == other.subqueries[i] for i, s in enumerate(self.subqueries)])


class WEmpty(WQuery):
    def check(self, value):
        return True

    def __repr__(self):
        return 'None'

    def to_list(self):
        return None

    def __eq__(self, other):
        return isinstance(other, WEmpty)


class WEq(PrimitiveWQuery):
    _operator = operator.eq
    _tag = 'eq'


class WNeq(PrimitiveWQuery):
    _operator = operator.ne
    _tag = 'neq'


class WLt(PrimitiveWQuery):
    _operator = operator.lt
    _tag = 'lt'


class WGt(PrimitiveWQuery):
    _operator = operator.gt
    _tag = 'gt'


class WLte(PrimitiveWQuery):
    _operator = operator.le
    _tag = 'lte'


class WGte(PrimitiveWQuery):
    _operator = operator.ge
    _tag = 'gte'


class WIn(PrimitiveWQuery):
    _tag = 'in'

    def check(self, value):
        return self.select(value) in self.argument


class WNin(PrimitiveWQuery):
    _tag = 'nin'

    def check(self, value):
        return self.select(value) not in self.argument


class WContains(PrimitiveWQuery):
    _operator = operator.contains
    _tag = 'contains'


class WNContains(WContains):  # FIXME: better solution for negation!
    _tag = 'ncontains'

    def check(self, value):
        return not super().check(value)


class WStartswith(PrimitiveWQuery):
    _tag = 'startswith'

    def check(self, value):
        return self.select(value).startswith(self.argument)


class WEndswith(PrimitiveWQuery):
    _tag = 'endswith'

    def check(self, value):
        return self.select(value).endswith(self.argument)


class WIs(PrimitiveWQuery):
    _operator = operator.is_
    _tag = 'is'


class WAnd(CompositeWQuery):
    _tag = 'and'

    def check(self, value):
        return all([s.check(value) for s in self.subqueries])


class WNot(CompositeWQuery):
    _tag = 'not'

    def check(self, value):
        return not self.subqueries[0].check(value)


class WOr(CompositeWQuery):
    _tag = 'or'

    def check(self, value):
        return any([s.check(value) for s in self.subqueries])


_primitive_queries = {cls._tag: cls for cls in [
    WEq, WNeq, WLt, WGt, WLte, WGte,
    WIn, WNin, WContains, WNContains, WStartswith, WEndswith,
    WIs,
]}

_composite_queries = {cls._tag: cls for cls in [WAnd, WNot, WOr]}


def parse_wt(wt):
    if wt is None:
        return WEmpty()
    elif wt[0] in _primitive_queries:
        return _primitive_queries[wt[0]](*wt[1:])
    elif wt[0] in _composite_queries:
        return _composite_queries[wt[0]](*[parse_wt(swt) for swt in wt[1:]])
    raise TypeError("Invalid query definition {}".format(repr(wt)))
