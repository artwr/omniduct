from omniduct.databases.base import DatabaseClient
from omniduct.databases.hiveserver2 import HiveServer2Client


class PySparkClient(DatabaseClient):

    PROTOCOLS = ['pyspark']
    DEFAULT_PORT = None

    def _init(self, app_name='omniduct', config=None, master=None, enable_hive_support=False):
        """
        Parameters:
            app_name (str): The application name of the SparkSession.
            config (dict or None): Any additional configuration to pass through
                to the SparkSession builder.
            master (str): The Spark master URL to connect to (only necessary
                if environment specified configuration is missing).
            enable_hive_support (bool): Whether to enable Hive support for the
                Spark session.

        Note: Pyspark must be installed in order to use this backend.
        """
        self.app_name = app_name
        self.config = config or {}
        self.master = master
        self.enable_hive_support = enable_hive_support
        self._spark_session = None

    # Connection management

    def _connect(self):
        from pyspark.sql import SparkSession

        builder = SparkSession.builder.appName(self.app_name)
        if self.master:
            builder.master(self.master)
        if self.enable_hive_support:
            builder.enableHiveSupport()
        if self.config:
            for key, value in self.config.items():
                builder.config(key, value)

        self._spark_session = builder.getOrCreate()

    def _is_connected(self):
        return self._spark_session is not None

    def _disconnect(self):
        self._spark_session.sparkContext.stop()

    # Database operations

    def _execute(self, statement, cursor=None, wait=True, **kwargs):
        assert wait is True, "This Spark backend does not support asynchronous operations."
        return SparkCursor(self._spark_session.sql(statement))

    def _table_list(self, **kwargs):
        return HiveServer2Client._table_list(self, **kwargs)

    def _table_exists(self, table, **kwargs):
        return HiveServer2Client._table_exists(self, table, **kwargs)

    def _table_desc(self, table, **kwargs):
        return HiveServer2Client._table_desc(self, table, **kwargs)

    def _table_head(self, table, n=10, **kwargs):
        return HiveServer2Client._table_head(self, table, n=n, **kwargs)

    def _table_props(self, table, **kwargs):
        return HiveServer2Client._table_props(self, table, **kwargs)


class SparkCursor(object):
    """
    This DBAPI2 compatible cursor wraps around a Spark DataFrame
    """

    def __init__(self, df):
        self.df = df
        self._df_iter = None

    @property
    def df_iter(self):
        if not getattr(self, '_df_iter'):
            self._df_iter = self.df.toLocalIterator()
        return self._df_iter

    arraysize = 1

    @property
    def description(self):
        return tuple([
            (name, type_, None, None, None, None, None)
            for name, type_ in self.df.dtypes
        ])

    @property
    def row_count(self):
        return -1

    def close(self):
        pass

    def execute(operation, parameters=None):
        pass

    def executemany(operation, seq_of_parameters=None):
        pass

    def fetchone(self):
        return [
            value or None
            for value in next(self.df_iter)
        ]

    def fetchmany(self, size=None):
        size = size or self.arraysize
        return [self.fetchone() for _ in range(size)]

    def fetchall(self):
        return list(self.df_iter)

    def setinputsizes(self, sizes):
        pass

    def setoutputsize(self, size, column=None):
        pass
