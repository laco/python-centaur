import asyncio
import functools
from .bridges import HTTPBridge, TESTBridge, BaseBridge


def describe_port(*descriptions):
    pass


class Adapter(object):
    def __init__(self, application):
        self.app = application
        self.f_ = self.app.f_


class Application(object):
    def __init__(self, ports=None, adapters=None, config=None):
        self.config = config or {}
        self.ports = ports or {}
        self.adapters = {
            aname: acls(self) for aname, acls in adapters.items() or {}}

        self.init_event_loop()

    def lookup_fn_name(self, fn_name):
        adapter, fname = fn_name.split('.')
        return getattr(self.adapters[adapter], fname)

    def init_event_loop(self):
        policy = asyncio.get_event_loop_policy()
        policy.get_event_loop().close()
        event_loop = policy.new_event_loop()
        policy.set_event_loop(event_loop)
        self.event_loop = event_loop
        return event_loop

    async def f_(self, fn_name, **kwargs):
        coro = self.lookup_fn_name(fn_name)
        ret = await coro(**kwargs)
        return ret

    async def run_in_executor(self, fn, *args, **kwargs):
        return await self.event_loop.run_in_executor(
            None, functools.partial(fn, *args, **kwargs))


__all__ = ["TESTBridge", "HTTPBridge", "BaseBridge",
           "Application"]
