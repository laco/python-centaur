import re
import functools
import inspect


class Types(object):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    LIST = "list"
    DICT = "dict"


class Rels(object):
    EQ = 'eq'
    NE = 'ne'
    GT = 'gt'
    LT = 'lt'
    GTE = 'gte'
    LTE = 'lte'

    LENGTH = 'length'
    LENGTH_MIN = 'length_min'
    LENGTH_MAX = 'length_max'
    REGEX = 'regex'

    ITEMS = 'items'
    FIELDS = 'fields'


class ValidationError(Exception):
    pass


class InvalidDataTypeDefinition(Exception):
    pass


class InvalidModuleDefinition(Exception):
    pass


class TypeMismatchError(ValidationError):
    pass


class InvalidValueError(ValidationError):
    pass


class InvalidIntegerValue(ValidationError):
    pass


def load_datatypes(module_list):
    ctx = _Context(module_list=module_list)
    return ctx


def def_datatype(type_, **kwargs):

    def _check_kwargs(type_, kwargs):
        for k in kwargs:
            if k not in _allowed_arguments_for(type_):
                raise InvalidDataTypeDefinition("Invalid argument {0} for datatype {1}".format(k, type_))
        return True

    _check_kwargs(type_, kwargs)
    dt = _Datatype()
    dt.type_ = type_
    dt.params = kwargs
    return dt


def datatype_from_dict(d):
    d_ = {k: v for k, v in d.items() if k != 'type'}
    type_ = d['type']
    return def_datatype(type_, **d_)


def module_from_dict(d):
    name = d.get("name")
    datatypes = d.get("datatypes", None)
    m = _Module(name=name, datatypes=datatypes)
    return m


def fulfill(value, datatype, _catch_exceptions=False):
    def _fulfill(value, datatype):
        return _check_type(value, datatype.type_) and _check_params(value, datatype.params)
    if _catch_exceptions is True:
        try:
            return _fulfill(value, datatype)
        except Exception as e:
            return e
    else:
        return _fulfill(value, datatype)


def validate_before_call(param, *args):
    _ctx, _args = _create_default_ctx(), None

    def _add_default_param_values(ba, sig):
        for param in sig.parameters.values():
            if param.name not in ba.arguments:
                ba.arguments[param.name] = param.default
        return ba

    def _param_is_not_empty(p):
        return p.annotation is not inspect._empty

    def _param_is_not_default(p, ba):
        return ba.arguments[p.name] != p.default

    def _datatype_from_annotation(p):
        if isinstance(p.annotation, (_Datatype, dict)):
            return _create_dt_if_not_dt(p.annotation)
        else:
            return _ctx.get_datatype(p.annotation)

    def _not_default_params_with_validation(sig, ba):
        for param in sig.parameters.values():
            if _param_is_not_empty(param) and _param_is_not_default(param, ba):
                dt_from_annotation = _datatype_from_annotation(param)
                if dt_from_annotation is not None:
                    yield param, dt_from_annotation

    def _validate_fn_params_by_annotations(fn, *args, **kwargs):
        sig = inspect.signature(fn)
        bound_arguments = _add_default_param_values(sig.bind(*args, **kwargs), sig)
        validation_results = [
            fulfill(
                bound_arguments.arguments[param.name],
                datatype_)
            for param, datatype_ in _not_default_params_with_validation(sig, bound_arguments)]
        return validation_results

    def _decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            _validate_fn_params_by_annotations(fn, *args, **kwargs)
            result = fn(*args, **kwargs)
            return result
        return wrapper
    if callable(param):
        return _decorator(param)
    else:
        _ctx, _args = param, args  # noqa
        return _decorator


def _allowed_arguments_for(type_):
    if type_ in [Types.INTEGER, Types.NUMBER]:
        return [Rels.EQ, Rels.NE, Rels.GT, Rels.LT, Rels.GTE, Rels.LTE]
    elif type_ in [Types.STRING]:
        return [Rels.EQ, Rels.NE, Rels.LENGTH, Rels.LENGTH_MIN, Rels.LENGTH_MAX, Rels.REGEX]
    elif type_ in [Types.LIST]:
        return [Rels.LENGTH, Rels.LENGTH_MIN, Rels.LENGTH_MAX, Rels.ITEMS]
    elif type_ in [Types.DICT]:
        return [Rels.FIELDS]


def _check_type(value, type_):
    if type_ == Types.STRING and isinstance(value, str):
        return True
    elif type_ in [Types.INTEGER, Types.NUMBER] and isinstance(value, (int, float)):
        return type_ == Types.NUMBER or (type_ == Types.INTEGER and _check_integer(value))
    elif type_ == Types.LIST and isinstance(value, (list, tuple)):
        return True
    elif type_ == Types.DICT and isinstance(value, dict):
        return True
    else:
        raise TypeMismatchError("Invalid value for {0}: {1} (type mismatch).".format(type_, value))


def _check_integer(value):
    "returns True if the value is a whole number"
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
        return True
    else:
        raise InvalidIntegerValue("{0} is not an integer.".format(value))


def _check_params(value, params):
    return all([_check_param(value, param, pvalue) for param, pvalue in params.items()])


def _check_param(value, param, pvalue):
    def _regex_fulfill(value, p):
        return re.match(p, value) is not None

    _param_check_fn_mapping = {
        Rels.GT: lambda value, p: value > p,
        Rels.LT: lambda value, p: value < p,
        Rels.LTE: lambda value, p: value <= p,
        Rels.GTE: lambda value, p: value >= p,
        Rels.NE: lambda value, p: value != p,
        Rels.EQ: lambda value, p: value == p,
        Rels.REGEX: _regex_fulfill
    }

    if param in _param_check_fn_mapping:
        ret = _param_check_fn_mapping[param](value, pvalue)
    elif param in [Rels.LENGTH, Rels.LENGTH_MAX, Rels.LENGTH_MIN]:
        length = len(value)
        if param == Rels.LENGTH:
            ret = _param_check_fn_mapping[Rels.EQ](length, pvalue)
        elif param == Rels.LENGTH_MAX:
            ret = _param_check_fn_mapping[Rels.LTE](length, pvalue)
        elif param == Rels.LENGTH_MIN:
            ret = _param_check_fn_mapping[Rels.GTE](length, pvalue)
    elif param == Rels.ITEMS:
        ret = all([fulfill(item, _create_dt_if_not_dt(pvalue)) for item in value])
    elif param == Rels.FIELDS:
        ret = all([fulfill(value[fkey], _create_dt_if_not_dt(fvalue)) for fkey, fvalue in pvalue.items()])
    else:
        ret = False
    if not ret:
        raise InvalidValueError("Invalid value {0} for definition {1} {2}".format(value, param, pvalue))
    else:
        return ret


def _create_dt_if_not_dt(p):
    if isinstance(p, _Datatype):
        return p
    elif isinstance(p, dict):
        return datatype_from_dict(p)
    else:
        raise InvalidDataTypeDefinition("Cannot create datatype from {0}".format(p))


def _instantiate_module_if_not_module(m):
    if isinstance(m, _Module):
        return m
    elif isinstance(m, dict):
        return module_from_dict(m)
    else:
        raise InvalidModuleDefinition("Cannot instantiate module from {0}".format(m))


class _Datatype(object):
    def __repr__(self):
        return "Datatype(\"{type_}\", {params})".format(type_=self.type_, params=self.params)


class _Module(object):
    def __init__(self, name, datatypes=None):
        self.name = name
        self._datatypes = {} if datatypes is None else \
                          {name: _create_dt_if_not_dt(dt) for name, dt in datatypes.items()}

    def get_datatype(self, datatype_name):
        return self._datatypes[datatype_name]

    def get_datatypes(self, datatype_names):
        return [self.get_datatype(dtn) for dtn in datatype_names or []]


class _Context(object):
    def __init__(self, module_list=None):
        self.modules = [_instantiate_module_if_not_module(m) for m in module_list or []]

    def _parse_datatype_name(self, datatype_name):
        n = datatype_name.split(":")
        if len(n) == 3:
            return n
        elif len(n) == 2:
            return None, n[0], n[1]
        elif len(n) == 1:
            return None, None, n[0]
        else:
            raise KeyError("Bad key for datatype: {0}".format(datatype_name))

    def _filter_modules(self, ns=None, mname=None):
        def _check_ns(module_, ns):
            return ns is None or ns == module_.ns

        def _check_mname(module_, mname):
            return mname is None or module_.name == mname

        return [
            m for m in self.modules
            if _check_ns(m, ns) and _check_mname(m, mname)
        ]

    def get_datatype(self, datatype_name):
        ns, mname, dname = self._parse_datatype_name(datatype_name)
        for m in self._filter_modules(ns, mname):
            try:
                return m.get_datatype(dname)
            except KeyError:
                continue
        raise KeyError("Datatype {0} not found in context.".format(datatype_name))

    def get_datatypes(self, datatype_names):
        return [self.get_datatype(dtn) for dtn in datatype_names or []]


def _email_regex():
    # email regex rules
    WSP = r'[ \t]'                                       # see 2.2.2. Structured Header Field Bodies
    CRLF = r'(?:\r\n)'                                   # see 2.2.3. Long Header Fields
    NO_WS_CTL = r'\x01-\x08\x0b\x0c\x0f-\x1f\x7f'        # see 3.2.1. Primitive Tokens
    QUOTED_PAIR = r'(?:\\.)'                             # see 3.2.2. Quoted characters
    FWS = r'(?:(?:' + WSP + r'*' + CRLF + r')?' + \
        WSP + r'+)'                                    # see 3.2.3. Folding white space and comments
    CTEXT = r'[' + NO_WS_CTL + \
        r'\x21-\x27\x2a-\x5b\x5d-\x7e]'              # see 3.2.3
    CCONTENT = r'(?:' + CTEXT + r'|' + \
        QUOTED_PAIR + r')'                        # see 3.2.3 (NB: The RFC includes COMMENT here
    # as well, but that would be circular.)
    COMMENT = r'\((?:' + FWS + r'?' + CCONTENT + \
              r')*' + FWS + r'?\)'                       # see 3.2.3
    CFWS = r'(?:' + FWS + r'?' + COMMENT + ')*(?:' + \
           FWS + '?' + COMMENT + '|' + FWS + ')'         # see 3.2.3
    ATEXT = r'[\w!#$%&\'\*\+\-/=\?\^`\{\|\}~]'            # see 3.2.4. Atom
    # ATOM = CFWS + r'?' + ATEXT + r'+' + CFWS + r'?'       # see 3.2.4
    DOT_ATOM_TEXT = ATEXT + r'+(?:\.' + ATEXT + r'+)*'    # see 3.2.4
    DOT_ATOM = CFWS + r'?' + DOT_ATOM_TEXT + CFWS + r'?'  # see 3.2.4
    QTEXT = r'[' + NO_WS_CTL + \
        r'\x21\x23-\x5b\x5d-\x7e]'                   # see 3.2.5. Quoted strings
    QCONTENT = r'(?:' + QTEXT + r'|' + \
               QUOTED_PAIR + r')'                        # see 3.2.5
    QUOTED_STRING = CFWS + r'?' + r'"(?:' + FWS + \
        r'?' + QCONTENT + r')*' + FWS + \
        r'?' + r'"' + CFWS + r'?'
    LOCAL_PART = r'(?:' + DOT_ATOM + r'|' + \
                 QUOTED_STRING + r')'                    # see 3.4.1. Addr-spec specification
    DTEXT = r'[' + NO_WS_CTL + r'\x21-\x5a\x5e-\x7e]'    # see 3.4.1
    DCONTENT = r'(?:' + DTEXT + r'|' + \
               QUOTED_PAIR + r')'                        # see 3.4.1
    DOMAIN_LITERAL = CFWS + r'?' + r'\[' + \
        r'(?:' + FWS + r'?' + DCONTENT + \
        r')*' + FWS + r'?\]' + CFWS + r'?'  # see 3.4.1
    DOMAIN = r'(?:' + DOT_ATOM + r'|' + \
        DOMAIN_LITERAL + r')'                       # see 3.4.1
    ADDR_SPEC = LOCAL_PART + r'@' + DOMAIN               # see 3.4.1
    VALID_ADDRESS_REGEXP = re.compile('^' + ADDR_SPEC + '$')
    return VALID_ADDRESS_REGEXP


def _create_default_ctx():
    ctx_ = load_datatypes([{
        'name': 'commons',
        'ns': 'centaur',
        'datatypes': {
            'email': {'type': Types.STRING, 'regex': _email_regex()}
        }}])
    return ctx_


default_ctx = _create_default_ctx()
