from typing import Optional
from collections import OrderedDict

import boto3

from mindsdb_sql.parser.ast.base import ASTNode

from mindsdb.integrations.libs.base import DatabaseHandler
from mindsdb.integrations.libs.response import (
    HandlerStatusResponse as StatusResponse
)
from mindsdb.integrations.libs.const import HANDLER_CONNECTION_ARG_TYPE as ARG_TYPE

from mindsdb.integrations.handlers.mysql_handler.mysql_handler import MySQLHandler
from mindsdb.integrations.handlers.postgres_handler.postgres_handler import PostgresHandler


class AuroraHandler(DatabaseHandler):
    """
    This handler handles connection and execution of the Firebird statements.
    """

    name = 'aurora'

    def __init__(self, name: str, connection_data: Optional[dict], **kwargs):
        """
        Initialize the handler.
        Args:
            name (str): name of particular handler instance
            connection_data (dict): parameters for connecting to the database
            **kwargs: arbitrary keyword arguments.
        """
        # TODO: check if using the same name parameter here and when instantiating the objects will be feasible
        # TODO: check if any of these other parameters like parse_sql are required
        super().__init__(name)
        self.parser = parse_sql
        self.dialect = 'aurora'
        self.connection_data = connection_data
        self.kwargs = kwargs

        self.connection = None
        self.is_connected = False

        database_engine = ""
        if 'db_engine' not in self.connection_data:
            database_engine = self.get_database_engine()

        if self.connection_data['db_engine'] == 'mysql' or database_engine == 'aurora':
            self.db = MySQLHandler(
                # TODO: check if using the same name parameter here again will be feasible
                name=name,
                connection_data=self.connection_data
            )
        elif self.connection_data['db_engine'] == 'postgresql' or database_engine == 'aurora-postgresql':
            self.db = PostgresHandler(
                # TODO: check if using the same name parameter here again will be feasible
                name=name,
                connection_data=self.connection_data
            )
        else:
            pass

    def get_database_engine(self):
        session = boto3.session.Session(
            aws_access_key_id=self.connection_data['aws_access_key_id'],
            aws_secret_access_key=self.connection_data['aws_secret_access_key']
        )

        rds = session.client('rds')

        response = rds.describe_db_clusters()

        return next(item for item in response if item["DBClusterIdentifier"] == self.connection_data['host'].split('.')[0])['Engine']

    def __del__(self):
        if self.is_connected is True:
            self.disconnect()

    def connect(self) -> StatusResponse:
        """
        Set up the connection required by the handler.
        Returns:
            HandlerStatusResponse
        """

        return self.db.connect()

    def disconnect(self):
        """
        Close any existing connections.
        """

        return self.db.disconnect()

    def check_connection(self) -> StatusResponse:
        """
        Check connection to the handler.
        Returns:
            HandlerStatusResponse
        """

        return self.db.check_connection()

    def native_query(self, query: str) -> StatusResponse:
        """
        Receive raw query and act upon it somehow.
        Args:
            query (str): query in native format
        Returns:
            HandlerResponse
        """

        return self.db.native_query(query)

    def query(self, query: ASTNode) -> StatusResponse:
        """
        Receive query as AST (abstract syntax tree) and act upon it somehow.
        Args:
            query (ASTNode): sql query represented as AST. May be any kind
                of query: SELECT, INTSERT, DELETE, etc
        Returns:
            HandlerResponse
        """

        return self.db.query(query)

    def get_tables(self) -> StatusResponse:
        """
        Return list of entities that will be accessible as tables.
        Returns:
            HandlerResponse
        """

        return self.db.get_tables()

    def get_columns(self, table_name: str) -> StatusResponse:
        """
        Returns a list of entity columns.
        Args:
            table_name (str): name of one of tables returned by self.get_tables()
        Returns:
            HandlerResponse
        """

        return self.db.get_columns(table_name)


connection_args = OrderedDict(
    user={
        'type': ARG_TYPE.STR,
        'description': 'The user name used to authenticate with the Amazon Aurora DB cluster.'
    },
    password={
        'type': ARG_TYPE.STR,
        'description': 'The password to authenticate the user with the Amazon Aurora DB cluster.'
    },
    database={
        'type': ARG_TYPE.STR,
        'description': 'The database name to use when connecting with the Amazon Aurora DB cluster.'
    },
    host={
        'type': ARG_TYPE.STR,
        'description': 'The host name or IP address of the Amazon Aurora DB cluster. NOTE: use \'127.0.0.1\' instead of \'localhost\' to connect to local server.'
    },
    port={
        'type': ARG_TYPE.INT,
        'description': 'The TCP/IP port of the Amazon Aurora DB cluster. Must be an integer.'
    },
    db_engine={
        'type': ARG_TYPE.STR,
        'description': "The database engine of the Amazon Aurora DB cluster. This can take one of two values: 'mysql' or 'postgresql'. This parameter is optional, but if it is not provided, 'aws_access_key_id' and 'aws_secret_access_key' parameters must be provided"
    },
    aws_access_key_id={
        'type': ARG_TYPE.STR,
        'description': "The access key for the AWS account. This parameter is optional and is only required to be provided if the 'db_engine' parameter is not provided."
    },
    aws_secret_access_key={
        'type': ARG_TYPE.STR,
        'description': "The secret key for the AWS account. This parameter is optional and is only required to be provided if the 'db_engine' parameter is not provided."
    },
)

connection_args_example = OrderedDict(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='password',
    database='database'
)