import asyncio
import functools


class Adapter(object):
    def __init__(self, application):
        self.app = application
        self.f_ = self.app.f_


class Application(object):
    def __init__(self, config=None, adapters=None):
        self.config = config or {}
        adapters = adapters or {}
        self.adapters = {aname: acls(self) for aname, acls in adapters.items()}
        self.event_loop = self._get_event_loop()

    def _get_event_loop(self):
        policy = asyncio.get_event_loop_policy()
        policy.get_event_loop().close()
        event_loop = policy.new_event_loop()
        policy.set_event_loop(event_loop)
        return event_loop

    def lookup_name(self, name):
        adapter_name, attrib_name = name.split('.')
        return getattr(self.adapters[adapter_name], attrib_name)

    async def f_(self, fn_name, **kwargs):
        coro = self.lookup_name(fn_name)
        return await coro(**kwargs)

    async def run_in_executor(self, fn, *args, **kwargs):
        return await self.event_loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))
