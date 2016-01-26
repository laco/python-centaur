import asyncio
from aiohttp import web


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
        async def _request_data(request):
            return await request.json()

        async def _handler(request):
            kwargs = {}
            coro = self._app.lookup_fn_name(fn_name)
            accepted_parameters = coro.__code__.co_varnames[:coro.__code__.co_argcount]
            print('aparam', accepted_parameters)
            for p in accepted_parameters:
                if p in request.match_info:
                    kwargs[p] = request.match_info[p]

            if '_data' in accepted_parameters:
                kwargs['_data'] = await _request_data(request)
            print('++++', accepted_parameters, kwargs)
            res = await self._app.f_(fn_name, **kwargs)
            return web.Response(text=str(res))  # content_type='text/html'
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


class TESTBridge(BaseBridge):

    def f_(self, fn_name, **kwargs):
        return self._app.event_loop.run_until_complete(
            self._app.f_(fn_name, **kwargs))
