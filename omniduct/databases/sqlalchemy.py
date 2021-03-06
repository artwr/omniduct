from __future__ import absolute_import

from .base import DatabaseClient
from .schemas import SchemasMixin


class SQLAlchemyClient(DatabaseClient, SchemasMixin):

    PROTOCOLS = ['sqlalchemy', 'firebird', 'mssql', 'mysql', 'oracle', 'postgresql', 'sybase']

    def _init(self, dialect=None, driver=None, database=''):

        assert self._port is not None, "Omniduct requires SQLAlchemy databases to manually specify a port, as " \
                                       "it will often be the case that ports are being forwarded."

        if self.protocol is not 'sqlalchemy':
            self.dialect = self.protocol
        else:
            self.dialect = dialect
        assert self.dialect is not None, "Dialect not specified."

        self.driver = driver
        self.database = database
        self.connection_fields += ('schema',)

        self.engine = None
        self.connection = None

    @property
    def db_uri(self):
        return '{dialect}://{login}@{host_port}/{database}'.format(
            dialect=self.dialect + ("+{}".format(self.driver) if self.driver else ''),
            login=self.username + (":{}".format(self.password) if self.password else ''),
            host_port=self.host + (":{}".format(self.port) if self.port else ''),
            database=self.database
        )

    def _connect(self):
        import sqlalchemy

        self.engine = sqlalchemy.create_engine(self.db_uri)
        self._sqlalchemy_metadata = sqlalchemy.MetaData(self.engine)

    def _is_connected(self):
        return self.engine is not None

    def _disconnect(self):
        self.engine = None
        self._sqlalchemy_metadata = None
        self._schemas = None

    def _execute(self, statement, query=True, cursor=None, **kwargs):
        if cursor:
            cursor.execute(statement)
        else:
            cursor = self.engine.execute(statement).cursor
        return cursor

    def _cursor_empty(self, cursor):
        return False

    def _table_list(self, **kwargs):
        return self.query("SHOW TABLES", **kwargs)

    def _table_exists(self, table, schema=None):
        return (self.table_list(renew=True, schema=schema)['Table'] == table).any()

    def _table_desc(self, table, **kwargs):
        return self.query("DESCRIBE {0}".format(table), **kwargs)

    def _table_head(self, table, n=10, **kwargs):
        return self.query("SELECT * FROM {} LIMIT {}".format(table, n), **kwargs)

    def _table_props(self, table, **kwargs):
        raise NotImplementedError
