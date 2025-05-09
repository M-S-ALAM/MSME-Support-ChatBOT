"""
run_query.py
=============================================
This module provides classes for managing a singleton database connection and executing SQL queries
against a SQLite database using SQLAlchemy and pandas. It is designed for use in chatbot and data
analysis pipelines where dynamic, thread-safe access to a database is required.

Classes:
    - DynamicDatabase: Singleton for managing the database engine connection.
    - DatabaseHandler: Executes SQL queries and returns results as pandas DataFrames or error messages.

Usage Example:
    handler = DatabaseHandler()
    result = handler.execute_query("SELECT * FROM my_table")
    if isinstance(result, pd.DataFrame):
        # process DataFrame
    else:
        # handle error message in result

"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Union

class DynamicDatabase:
    """
    Singleton class to manage a dynamic database connection.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self.engine = None
        self.db_path = os.path.join('Database', 'manufacturing_projects.db')
        # Ensure the Database directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self._initialized = True

    def connect(self):
        """
        Establishes a connection to the SQLite database.
        """
        if not self.engine:
            try:
                self.engine = create_engine(f'sqlite:///{self.db_path}')
            except Exception as e:
                raise RuntimeError(f"Failed to connect to database: {e}")

    def get_engine(self):
        """
        Returns the SQLAlchemy engine, connecting if necessary.
        """
        if not self.engine:
            self.connect()
        return self.engine

class DatabaseHandler:
    """
    Handles execution of SQL queries using the dynamic database engine.
    """
    def __init__(self):
        self.engine = DynamicDatabase().get_engine()

    def execute_query(self, query: str) -> Union[pd.DataFrame, dict]:
        """
        Executes a SQL query and returns a DataFrame or error message.
        Returns:
            pd.DataFrame if query is successful and returns data,
            dict with 'message' or 'error' otherwise.
        """
        if not query or not isinstance(query, str) or not query.strip():
            return {"message": "No valid SQL query provided."}
        try:
            df = pd.read_sql(sql=text(query), con=self.engine)
            if df.empty:
                return {"message": "Query executed successfully but returned no data."}
            return df
        except SQLAlchemyError as e:
            return {"message": f"Database error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}