import centaur


core_spec = centaur.describe_port(
    ("hello", []),
    ("add_numbers", ['a', 'b']),
)


class CoreAdapter(centaur.Adapter):
    __port__ = core_spec

    async def hello(self):
        return "Hello World!"

    async def add_numbers(self, a: int, b: int):
        return a + b


centaur_app = centaur.Application(
    ports={
        'core': core_spec
    },
    adapters={
        'core': CoreAdapter
    })

app = centaur.WSGIBridge(
    centaur_app,
    routes=[
        ('/hello', centaur.HTTP_GET, 'core.hello'),
        ('/add_numbers/{a}/{b}/', centaur.HTTP_GET, 'core.add_numbers'),
    ])

# app.initialize()
