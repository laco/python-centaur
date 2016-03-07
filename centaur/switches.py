from centaur.queries import parse_wt


class SwitchStates(object):
    GLOBAL_ENABLED = 'GLOBAL_ENABLED'
    GLOBAL_DISABLED = 'GLOBAL_DISABLED'
    SELECTIVE = 'SELECTIVE'


class SwitchBoard(object):
    def __init__(self):
        self._switches = {}

    def is_enabled(self, switch_name, *args, **kwargs):
        try:
            return self._switches[switch_name].is_enabled(*args, **kwargs)
        except KeyError:
            return False

    def add_switch(self, name, *args, **kwargs):
        self._switches[name] = Switch(name, *args, **kwargs)

    def get_context(self, overwrite=None, *args, **kwargs):
        def _overwrite(overwrite, ctx):
            return {**ctx, **overwrite} if overwrite is not None else ctx
        return _overwrite(
            overwrite,
            {name: self._switches[name].is_enabled(*args, **kwargs) for name in self._switches})


class Switch(object):
    def __init__(self, name,
                 description=None,
                 state=SwitchStates.GLOBAL_DISABLED,
                 owner=None,
                 expire_date=None,
                 created_at=None, conditions=None):
        self.name = name
        self.description = description
        self.state = state
        self.owner = owner
        self.expire_date = expire_date
        self.created_at = created_at
        self.conditions = conditions
        self._predicate = parse_wt(self.conditions).as_predicate() \
            if conditions is not None else lambda value: False

    def is_enabled(self, *args, **kwargs):
        if self.state == SwitchStates.GLOBAL_ENABLED:
            return True
        elif self.state == SwitchStates.GLOBAL_DISABLED:
            return False
        elif self.state == SwitchStates.SELECTIVE:
            return self._predicate(kwargs)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        keys = ['name', 'description', 'state', 'owner', 'expire_date', 'created_at', 'conditions']
        return {k: getattr(self, k, None) for k in keys}


class InMemorySwitchManager(object):
    def __init__(self, initial_state):
        self.state = initial_state

    def load_from_database(self):
        return {s: Switch.from_dict(self.state[s]) for s in self.state}

    def store_to_database(self, switches):
        self.state = {s: switches[s].to_dict() for s in switches}


class NimoySchemaSwitchManager(object):  # noqa
    def __init__(self, db_conn, schema_name):
        self.db_conn = db_conn
        self.schema_name = schema_name

    def load_from_database(self):
        return {s['name']: Switch.from_dict(s) for s in self._db_get_items()}

    def _db_get_items(self):
        return self.db_conn.scan(self.schema_name, _w=None, limit=9999)

    def _db_put_item(self, switch_dict):
        return self.db_conn.put_item(self.schema_name, switch_dict, overwrite=True)

    def store_to_database(self, switches):
        return {s: self._db_put_item(switches[s].to_dict()) for s in switches}


class PersistentSwitchBoard(SwitchBoard):
    def __init__(self, manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager
        self._switches = self.manager.load_from_database()

    def add_switch(self, name, *args, **kwargs):
        super().add_switch(name, *args, **kwargs)
        self.manager.store_to_database(self._switches)
