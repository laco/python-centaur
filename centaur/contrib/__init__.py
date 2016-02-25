import centaur
from centaur.safe_import import safe_import


DatabaseConnection = safe_import('nimoy.connection', 'DatabaseConnection', msg='Plz. install nimoy package for this Adapter')


class NimoyAdapter(centaur.Adapter):
    def __init__(self, application):
        super().__init__(application)
        nimoy_config = self.app.config.get('nimoy_config', {})
        nimoy_schemas = self.app.config.get('nimoy_schemas', {})
        self.db = DatabaseConnection(schema=nimoy_schemas, **nimoy_config)

    async def get_item(self, schema_name, _id, **kw):
        return await self.app.run_in_executor(
            self.db.get_item, schema_name, _id, **kw)

    async def put_item(self, schema_name, _data, **kw):
        return await self.app.run_in_executor(
            self.db.put_item, schema_name, _data, **kw)

    async def delete_item(self, schema_name, _id, **kw):
        return await self.app.run_in_executor(
            self.db.delete_item, schema_name, _id, **kw)

    async def query(self, schema_name, _w, limit=500, **kw):
        return await self.app.run_in_executor(
            self.db.query, schema_name, _w, limit, **kw)

    async def query_count(self, schema_name, _w, **kw):
        return await self.app.run_in_executor(
            self.db.query_count, schema_name, _w, **kw)

    async def scan(self, schema_name, _w, limit=500, **kw):
        return await self.app.run_in_executor(
            self.db.scan, schema_name, _w, limit, **kw)

    async def uuid(self):
        return await self.app.run_in_executor(self.db.uuid)
