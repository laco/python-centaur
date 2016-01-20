import pytest
import os

from inspect import signature
from centaur.services import load_service, _Service, create_action_fn
from centaur.datatypes.classes import _Module
from centaur.datatypes import fulfill, ValidationError


sample_service_def = {
    'name': 'sample',
    'description': 'Sample service definition',
    'datatypes': {
        'sampleID': {'type': 'string', 'length_min': 5},
    },
    'interface': {
        'sample_action': {
            'description': 'Sample action with parameters',
            'request': {
                'method': 'GET',
                'url': '/sample/',
                'params': {'id': 'sampleID'}
            },
            'response': {
                'text': {'type': 'string'}
            }
        }
    }
}

sample_service_yml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_service.yml")


def test_def_service_returns_a_module():
    service = load_service(sample_service_def)
    assert isinstance(service, _Module)
    assert isinstance(service, _Service)
    sample_id_dt = service.get_datatype('sampleID')
    assert fulfill('aaaaa', sample_id_dt)
    assert service.actions is not None
    assert 'sample_action' in service.actions


def test_load_service_from_file():
    service = load_service(sample_service_yml_file)
    assert service is not None


def test_create_action_fn():
    service = load_service(sample_service_def)
    action_def = sample_service_def['interface']['sample_action']

    action_fn = create_action_fn('sample_action', action_def, dt_ctx=service.as_ctx())
    action_fn_sig = signature(action_fn)

    assert(action_fn) is not None
    assert 'id' in action_fn_sig.parameters
    with pytest.raises(ValidationError):
        action_fn('aaa')

    with pytest.raises(ValidationError):
        service.sample_action(id='aaa')

    with pytest.raises(TypeError):
        service.sample_action(id='aaaaa', xxx=123)

# def test_create_fn_for_request():
#     sample_fn = create_fn_for_request(
#         method='GET', url='/sample/', base_url='http://localhost:5000', params={'id': {'type': 'string'}})
#     assert sample_fn is not None
#     assert callable(sample_fn) is True
#     assert sample_fn(id='somethin') is not None


# def test_create_sample_client_object():
#     service_def = {
#         'name': 'sample',
#         'description': 'Sample service definition',
#         'datatypes': {
#             'sampleID': {'type': 'string', 'length_min': 5},
#         },
#         'interface': {
#             'sample_action': {
#                 'description': 'Sample action with parameters',
#                 'request': {
#                     'method': 'GET',
#                     'url': '/sample/',
#                     'params': {'id': 'sampleID'}
#                 },
#                 'response': {
#                     'text': {'type': 'string'}
#                 }
#             }
#         }
#     }
#     client = SyncHttpClient.from_dict(service_def, base_url='http://localhost:5000')
#     assert client.name == 'sample'
#     assert client.description == 'Sample service definition'
#     assert client.base_url == 'http://localhost:5000'
#     # assert hasattr(client, 'sample_action') is True
