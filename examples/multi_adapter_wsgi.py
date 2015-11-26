import centaur

core_spec = centaur.describe_port(
    ("get_book", ["_id"]))

backend_spec = centaur.describe_port(
    ("get_item", ["table", "_id"]))


class CoreAdapter(centaur.Adapter):
    __port__ = core_spec

    async def get_book(self, cn, _id):
        return cn.f_('backend.get_item', table='book', _id=_id)


_tables = {}


class BackendAdapter(centaur.Adapter):
    __port__ = backend_spec

    async def get_item(self, table, _id):
        return _tables.get(table, {}).get(_id, None)


centaur_app = centaur.Application(ports={'core': core_spec, 'backend': backend_spec},
                                  adapters={'core': CoreAdapter, 'backend': BackendAdapter})


app = centaur.WSGIBridge(centaur_app, routes=[
    ('/book/{_id}', centaur.HTTP_GET, 'core.get_book')])
