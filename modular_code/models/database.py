import os
from sqlalchemy import MetaData, Table, text
from modular_code.config import DbSqlAlchemy


class DynamicDatabase:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return  # Avoid re-initialization in singleton
        self.engine = None
        self.connection = None
        self.db_type = DbSqlAlchemy.db_type
        self._initialized = True

    def connect(self):
        """Establish a connection to the specified database."""
        if self.connection:
            return  # Already connected

        if self.db_type in ["mysql", "postgresql", "oracle", "sqlite"]:
            connection_string = self._get_sql_connection_string()
            self._import_sqlalchemy()
            self.engine = sqlalchemy.create_engine(connection_string)
            self.connection = self.engine.connect()
        elif self.db_type == "mongodb":
            self.connection = self._get_mongodb_connection()
        elif self.db_type == "sqlite":
            # Correct SQLite path handling
            return f"sqlite:///{os.path.join(DbSqlAlchemy.db_path, dbname)}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        if not self.connection:
            raise ConnectionError("Failed to establish a database connection.")

    def _get_sql_connection_string(self):
        """Generate SQL connection string."""
        user = DbSqlAlchemy.user
        password = DbSqlAlchemy.password
        host = DbSqlAlchemy.host
        port = DbSqlAlchemy.port
        dbname = DbSqlAlchemy.db_name

        if self.db_type == "mysql":
            self._import_pymysql()
            return f"mysql+pymysql://{user}:{password}@{host}/{dbname}"
        elif self.db_type == "postgresql":
            self._import_psycopg2()
            return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        elif self.db_type == "oracle":
            self._import_cx_oracle()
            return f"oracle+cx_oracle://{user}:{password}@{host}:{port}/?service_name={dbname}"
        elif self.db_type == "sqlite":
            return f"sqlite:///{dbname}"
        else:
            raise ValueError(f"Unsupported SQL database type: {self.db_type}")

    def _get_mongodb_connection(self):
        """Establish a MongoDB connection."""
        self._import_pymongo()
        user = os.environ.get("MONGODB_USER")
        password = os.environ.get("MONGODB_PASSWORD")
        host = os.environ.get("MONGODB_HOST", "localhost")
        port = os.environ.get("MONGODB_PORT", "27017")
        dbname = os.environ.get("MONGODB_DBNAME")

        if not all([user, password, host, port, dbname]):
            raise EnvironmentError("Missing MongoDB environment variables.")

        connection_string = f"mongodb://{user}:{password}@{host}:{port}/{dbname}"
        client = MongoClient(connection_string)
        return client[dbname]

    # Conditional imports
    def _import_sqlalchemy(self):
        global sqlalchemy
        import sqlalchemy

    def _import_pymysql(self):
        import pymysql

    def _import_psycopg2(self):
        import psycopg2

    def _import_cx_oracle(self):
        import cx_Oracle  # Fixed capitalization

    def _import_pymongo(self):
        global MongoClient
        from pymongo import MongoClient
