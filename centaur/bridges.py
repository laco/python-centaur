import datetime
import decimal
import json
from aiohttp import web
from centaur.utils import select_params_for_fn
from centaur.datatypes import ValidationError


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
            try:
                res = await self._app.f_(fn_name, **select_params_for_fn(kwargs, coro))
                if not isinstance(res, web.Response):
                    return web.Response(text=to_json(res), content_type='application/json')
                else:
                    return res
            except ValidationError as res:
                return web.Response(text=to_json({'error': str(res)}), content_type='application/json', status=400)
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
    for k, v in request.cookies.items():
        print('from cookies', k, v)
        ret[k] = v
#    for k, v in request.headers.items():
#        ret[k] = v
    ret['_data'] = await _request_data(request)

    # special values
    ret['_request'] = request
    ret['_cookies'] = request.cookies
    ret['_headers'] = request.headers
    return ret


class TESTBridge(BaseBridge):

    def f_(self, fn_name, **kwargs):
        return self._app.event_loop.run_until_complete(
            self._app.f_(fn_name, **kwargs))


try:
    from bson import ObjectId
except ImportError:
    ObjectId = None

try:
    from delorean import Delorean
except ImportError:
    Delorean = None

try:
    import numpy as np
except ImportError:
    np = None


class EnhancedEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif (ObjectId is not None) and isinstance(obj, ObjectId):
            return str(obj)
        elif (Delorean is not None) and isinstance(obj, Delorean):
            return obj.datetime.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(str(obj))
        elif (np is not None) and hasattr(obj, "dtype") and 'numpy' in str(type(obj)):
            try:
                return np.asscalar(obj)
            except:  # Exception as e:
                pass  # print(e)
            try:
                npn = obj(0)
                return npn.item()
            except:  # Exception as e:
                pass  # print(e)
        else:
            return super(EnhancedEncoder, self).default(obj)


def to_json(data, ensure_ascii=True):
    return json.dumps(data, cls=EnhancedEncoder, ensure_ascii=ensure_ascii)
