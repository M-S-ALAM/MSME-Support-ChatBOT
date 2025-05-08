"""
inference.py
============
This module provides a unified interface for running natural language to SQL inference,
executing the SQL query, and optionally generating a visualization based on the results.
"""

# Use relative imports for package context, or adjust sys.path for script execution
import os
import sys
print(sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))))

from sql_query_generation import SQLQueryGenerator
from src.mcp.run_query import DatabaseHandler
from src.mcp.generate_plot import VisualizationEngine
from typing import Optional, Dict, Any
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from src.utils.constant import Constants, OpenAIConfig, DbSqlAlchemyConstant

class InferenceEngine:
    """
    Orchestrates the process of:
    1. Generating SQL from a natural language query.
    2. Executing the SQL query.
    3. Optionally generating a visualization from the result.
    """

    def __init__(
        self,
        sql_generator: SQLQueryGenerator = None,
        db_handler: DatabaseHandler = None,
        viz_engine: VisualizationEngine = None,
        table_schemas: dict = None
    ):
        self.sql_generator = sql_generator or SQLQueryGenerator()
        self.db_handler = db_handler or DatabaseHandler()
        self.viz_engine = viz_engine or VisualizationEngine()
        self.table_schemas = table_schemas or {}

    def run(self, user_query: str, visualize: bool = False):
        """
        Runs the full inference pipeline:
        - Converts user_query to SQL.
        - Executes the SQL.
        - Optionally generates a visualization.

        Returns:
            dict: {
                "sql": str or None,
                "data": pd.DataFrame or dict,
                "visualization": plotly figure or None
            }
        """
        sql = self.sql_generator.generate_sql_query(user_query, self.table_schemas)
        if not sql:
            return {
                "sql": None,
                "data": {"message": "Could not generate SQL for the query."},
                "visualization": None
            }

        data = self.db_handler.execute_query(sql)
        visualization = None

        # Check if data is a pandas DataFrame for visualization
        try:
            import pandas as pd
            is_dataframe = isinstance(data, pd.DataFrame)
        except ImportError:
            is_dataframe = False

        if visualize and is_dataframe:
            output_type = self.viz_engine.suggest_output_type(data, user_query)
            if output_type == "plot":
                visualization = self.viz_engine.generate_chart(data)

        return {
            "sql": sql,
            "data": data,
            "visualization": visualization
        }
    

if __name__ == "__main__":
    # Example usage
    inference_engine = InferenceEngine()
    result = inference_engine.run("Show me the sales trend over time", visualize=True)
    print(result)
