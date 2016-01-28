import json
from aiohttp import web
from centaur.utils import select_params_for_fn


class BaseBridge(object):
    def __init__(self, application):
        self._app = application


class HTTPBridge(BaseBridge):
    def __init__(self, application):
        super().__init__(application)
        self._aiohttp_app = web.Application()

    def add_route(self, method, path, fn_name, *args, **kwargs):
        return self._aiohttp_app.router.add_route(
            method, path, self._http_handler_for(fn_name), *args, **kwargs)

    def add_routes(self, *routes):
        for arg in routes:
            print(arg)
            self.add_route(*arg)

    def _http_handler_for(self, fn_name):

        async def _handler(request):
            kwargs = await create_ctx_from_request(request)
            coro = self._app.lookup_name(fn_name)
            print(select_params_for_fn(kwargs, coro))
            res = await self._app.f_(fn_name, **select_params_for_fn(kwargs, coro))
            return web.Response(text=json.dumps(res), content_type='application/json')
        return _handler

    def run_server(self, host="0.0.0.0", port=8888):
        loop = self._app.event_loop
        handler = self._aiohttp_app.make_handler()
        f = loop.create_server(handler, host, port)
        srv = loop.run_until_complete(f)
        print('serving on', srv.sockets[0].getsockname())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(handler.finish_connections(1.0))
            srv.close()
            loop.run_until_complete(srv.wait_closed())
            loop.run_until_complete(self._aiohttp_app.finish())
            loop.close()


async def create_ctx_from_request(request):
    async def _request_data(request):
        try:
            return await request.json()
        except json.JSONDecodeError:
            return None
    ret = {}
    ret.update(request.match_info)
    ret['_data'] = await _request_data(request)
    return ret


class TESTBridge(BaseBridge):

    def f_(self, fn_name, **kwargs):
        return self._app.event_loop.run_until_complete(
            self._app.f_(fn_name, **kwargs))
