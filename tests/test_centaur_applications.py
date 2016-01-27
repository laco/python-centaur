import pytest
from centaur.applications import Application, Adapter


@pytest.fixture
def sample_application():
    return Application(adapters={'sample': SampleAdapter})


class SampleAdapter(Adapter):
    sample_attrib = 'sample'

    async def sample_fn(self, p):
        return p


async def sample_coro():
    return 'OK'


def test_empty_application():
    app = Application()
    assert app is not None


def test_sample_adapter(sample_application):
    app = sample_application
    assert 'sample' in app.adapters and isinstance(app.adapters['sample'], SampleAdapter)
    assert app.adapters['sample'].app == app
    assert app.lookup_name('sample.sample_attrib') == 'sample'


def test_application_has_event_loop():
    app = Application()
    coro = sample_coro()
    assert app.event_loop.run_until_complete(coro) is 'OK'


def test_application_call_adapter_method(sample_application):
    assert sample_application.event_loop.run_until_complete(sample_application.f_('sample.sample_fn', p='test')) == 'test'


def test_application_with_two_adatpers():
    class S1(Adapter):
        async def fn_one(self, a):
            return a * self.app.config.get('multiply_by', 2)

    class S2(Adapter):
        async def fn_two(self, b):
            return await self.f_('s1.fn_one', a=b)

    app = Application(adapters={'s1': S1, 's2': S2})
    assert app.event_loop.run_until_complete(app.f_('s2.fn_two', b=10)) == 20

    app = Application(config={'multiply_by': 3}, adapters={'s1': S1, 's2': S2})
    assert app.event_loop.run_until_complete(app.f_('s2.fn_two', b=10)) == 30


def test_application_run_in_executor():
    def blocking_function(a, b):
        import time
        time.sleep(0.3)
        return a + b
    app = Application()
    assert app.event_loop.run_until_complete(app.run_in_executor(blocking_function, a=10, b=10)) == 20
