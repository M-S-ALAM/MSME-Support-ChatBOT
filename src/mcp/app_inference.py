"""
inference.py
============
This module provides a unified interface for running natural language to SQL inference,
executing the SQL query, and optionally generating a visualization based on the results.
"""

# Use relative imports for package context, or adjust sys.path for script execution
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sql_query_generation import SQLQueryGenerator
from src.mcp.run_query import DatabaseHandler
from inference import get_llm_response
from src.mcp.generate_plot import VisualizationEngine, remove_sensitive_columns
from tabulate import tabulate
from src.mcp.classifier_greetings import GreetingClassifier

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
        self.classifier = GreetingClassifier(self.sql_generator)

    def run(self, user_query: str, visualize: bool = False):
        """
        Runs the full inference pipeline:
        - Classifies user_query as greeting or question.
        - If greeting, returns greeting message.
        - If question, converts to SQL, executes, and optionally visualizes.
        """
        classification_result = self.classifier.classify(user_query)
        if isinstance(classification_result, tuple) and classification_result[0] == "N/A":
            # It's a greeting or unclassified
            return {
                "sql": None,
                "data": classification_result[1],
                "visualization": None
            }

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
    visualization = VisualizationEngine()
    print("Text-to-SQL Chatbot (Type 'exit' to quit)\n")

    while True:
        user_input = input("Enter your natural language query: ").strip()

        if user_input.lower() == 'exit':
            print("Exiting...")
            break

        # inference_engine.run returns a dict with keys: "sql", "data", "visualization"
        result = inference_engine.run(user_input)
        sql_query = result.get("sql")
        data = result.get("data")

        if sql_query is None or data is None:
            if isinstance(data, dict) and "message" in data:
                print(f"\n{data['message']}\n")
            else:
                print("\n⚠️ Could not process the input.\n")
            continue

        if isinstance(data, dict):
            if "error" in data:
                print("\n❌ Error:", data["error"])
            elif "message" in data:
                print(f"\n{data['message']}\n")
            continue

        if isinstance(data, pd.DataFrame):
            clean_result = remove_sensitive_columns(data)
            output_type = visualization.suggest_output_type(clean_result, user_input)

            if output_type == 'text':
                summary = get_llm_response(user_input, clean_result.to_dict())
                print("\n📝 Insight Summary:\n", summary)

            elif output_type == 'table':
                print("\n📋 Table Output:\n")
                print(tabulate(clean_result, headers='keys', tablefmt='pretty'), "\n")

            elif output_type == 'plot':
                fig = visualization.generate_chart(clean_result)
                if fig:
                    fig.show()
                else:
                    print("⚠️ Plot could not be generated. Showing table instead.\n")
                    print(tabulate(clean_result, headers='keys', tablefmt='pretty'), "\n")
        else:
            print("\n⚠️ Unexpected result format.\n")

        print("\n🛠️ SQL Query used:\n", sql_query)
