from centaur.datatypes.context import _Module
from inspect import Signature, Parameter
from centaur.datatypes import validate_args


def load_service(d, client=None):
    if isinstance(d, dict):
        service = _Service.from_dict(d)
    elif isinstance(d, str):
        service = _Service.from_file(d)
    service.client = client
    return service


def create_action_fn(name, action_def, dt_ctx, client=None):
    action_signature = _param_signature_for_action_def(action_def)

    def action_fn(*args, **kwargs):
        barguments = action_signature.bind(*args, **kwargs)
        if client is not None:
            return client.request(barguments)

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


class _Service(_Module):

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
            return create_action_fn(name, self.actions[name], self.ctx, client=self.client)

    def construct_request(self, *args, **kwargs):
        return {}


class _Response(object):
    text = 'OK'


class FakeHttpClient(object):
    def add_response(self, *args, **kwargs):
        return self

    def request(self, request):
        return _Response()
