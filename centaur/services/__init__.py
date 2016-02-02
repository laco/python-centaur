from centaur.datatypes.context import _Module
from inspect import Signature, Parameter
from centaur.datatypes import validate_args


def load_service(d):
    if isinstance(d, dict):
        return _Service.from_dict(d)
    elif isinstance(d, str):
        return _Service.from_file(d)


def create_action_fn(name, action_def, dt_ctx, request_cls=None):
    action_signature = _param_signature_for_action_def(action_def)

    def action_fn(*args, **kwargs):
        barguments = action_signature.bind(*args, **kwargs)
        if request_cls is not None:
            return request_cls.process_response(request_cls.make_request(barguments))

    action_fn.__signature__ = action_signature
    action_fn.__name__ = name
    return validate_args(action_fn, ctx=dt_ctx)


def _param_signature_for_action_def(action_def, dt_ctx=None):
    def _create_parameter(name, datatype):
        return Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, annotation=datatype)

    params = []
    params.extend(
        [_create_parameter(name, dt) for name, dt in action_def['request'].get('params', {}).items()])
    return Signature(params)


# def create_fn_for_request(method, url, base_url=None, params=None):

#     def request_fn(*args, **kwargs):
#         pass


# class _Request(object):
#     def __init__(self, method, url, params=None, json=None):
#         pass


# class Action(object):
#     def __init__(self, name, description=None, request_def, response_def)

# def create_action_fn(i_def):
#     description = i_def['
#     request_def = i_def['request']
#     response_def = i_def['response']

#     method = i_def['method'].lower()


class _Service(_Module):
    # def __init__(self, name, description=None, base_url=None):
    #     self.name = name
    #     self.description = description
    #     self.base_url = base_url
    #     self.actions = {}

    # @classmethod
    # def from_dict(cls, sd_dict, base_url=None):
    #     name, description = [sd_dict.get(k, None) for k in ['name', 'description']]
    #     ret = cls(name=name, description=description, base_url=base_url)
    #     interface_def = sd_dict.get('interface')

    #     ret.datatypes_ctx = load_datatypes(module_list=[{
    #         'name': name,
    #         'description': description,
    #         'ns': sd_dict.get('ns'),
    #         'datatypes': sd_dict.get('datatypes')}])
    #     [ret.add_action(k, v) for k, v in interface_def.items()]
    #     return ret

    # def add_action(self, name, action_def):
    #     self.actions[name] = action_def

    # def __getattr__(self, name):
    #     if name in self.actions:
    #         return self._fn_for_interface(self.actions[name])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {}

    @classmethod
    def from_dict(cls, d):
        instance = super().from_dict(d)
        interface_def = d.get('interface')
        for action, action_def in interface_def.items():
            instance._add_action(action, action_def)
        return instance

    def _add_action(self, name, action_def):
        self.actions[name] = action_def

    def __getattr__(self, name):
        if name in self.actions:
            return create_action_fn(name, self.actions[name], self.as_ctx(), request_cls=None)


class SyncHttpClient(object):

    def __init__(self, name, description=None, base_url=None):
        self.name = name
        self.description = description
        self.base_url = base_url

    @classmethod
    def from_dict(cls, sd_dict, base_url=None):
        name, description = [sd_dict.get(k, None) for k in ['name', 'description']]
        ret = cls(name=name, description=description, base_url=base_url)
        interface_def = sd_dict.get('interface')

        ret.interface_def = interface_def
        return ret

    def __getattr__(self, name):
        if name in self.interface_def:
            return self._fn_for_interface(self.interface_def[name])

    def _fn_for_interface(self, i_def):
        pass
