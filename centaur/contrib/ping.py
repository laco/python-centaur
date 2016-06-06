import centaur
from datetime import datetime

# ping_spec = centaur.describe_port(
#     ('ping', []))


class PingAdapter(centaur.Adapter):
    # __port__ = ping_spec

    async def ping(self):
        print("in ping")
        return {'success': True, 'now': datetime.utcnow()}

    async def pong(self):
        print("in pong")
        return await self.app.f_('ping.ping')
