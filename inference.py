"""
Text-to-SQL Chatbot CLI Tool using OpenAI and SQLite.

Modules:
- DynamicDatabase: Singleton for managing a persistent SQLite engine.
- DatabaseHandler: Executes SQL queries using SQLAlchemy.
- LLMChatBot: Classifies input, generates SQL, and returns query results.
- main(): CLI interface for interactive usage.
"""

import os
import sys
import pandas as pd
from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from tabulate import tabulate
from typing import List, Union, Tuple

# Enable imports from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.constant import (
    History_Approach,
    UI_constants,
    DBConstant,
    OpenAIConfig
)
from src.codes.sql_query_generation import SQLQueryGenerator

# Global OpenAI client for LLM responses
llm_client = OpenAI(api_key=OpenAIConfig.OpenAI_API_KEY)

# Before any code that writes to '/home/shahbaz/Project/ChatBOT_Walmart/logs/sql_query_generator'
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../logs/sql_query_generator')
os.makedirs(log_dir, exist_ok=True)

# -------------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------------
def get_llm_response(query, value):
    prompt = f"The user asked: '{query}'. The result from the database is '{value}'. Provide a simple summary in plain english"
    try:
        response = llm_client.chat.completions.create(
            model=OpenAIConfig.OpenAI_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant providing insights based on database query results. Expect the user is non technical."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=OpenAIConfig.OpenAI_max_tokens,
            temperature=OpenAIConfig.OpenAI_temperature,
            top_p=OpenAIConfig.OpenAI_top_p
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Failed to generate insight: {e}"

def remove_sensitive_columns(result):
    columns_to_remove = {
        "customer_id", "employee_id", "project_id", "department_id",
        "invoice_id", "payment_id", "task_id", "time_entry_id"
    }
    if isinstance(result, pd.DataFrame):
        return result.drop(columns=[col for col in columns_to_remove if col in result.columns], errors='ignore')
    elif isinstance(result, list) and result and isinstance(result[0], dict):
        return [{k: v for k, v in row.items() if k not in columns_to_remove} for row in result]
    return result

# -------------------------------------------------------------------------
# Singleton Class: DynamicDatabase
# -------------------------------------------------------------------------
class DynamicDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.engine = None
        self.db_path = 'Database/manufacturing_projects.db'
        self._initialized = True

    def connect(self):
        if not self.engine:
            self.engine = create_engine(f'sqlite:///{self.db_path}')

    def get_engine(self):
        if not self.engine:
            self.connect()
        return self.engine

# -------------------------------------------------------------------------
# DatabaseHandler
# -------------------------------------------------------------------------
class DatabaseHandler:
    def __init__(self):
        self.engine = DynamicDatabase().get_engine()

    def execute_query(self, query: str) -> Union[pd.DataFrame, dict]:
        if query is None:
            return {"message": "The requested information does not exist in the database schema."}
        try:
            df = pd.read_sql(sql=text(query), con=self.engine)
            return df
        except SQLAlchemyError:
            return {"message": "Sorry, cannot answer with the current database information."}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

# -------------------------------------------------------------------------
# VisualizationEngine
# -------------------------------------------------------------------------
class VisualizationEngine:
    def __init__(self, llm=None):
        self.supported_types = ['line', 'bar', 'scatter', 'histogram', 'pie', 'trend']
        self.llm = llm or OpenAI(api_key=OpenAIConfig.OpenAI_API_KEY)

    def suggest_output_type(self, df: pd.DataFrame, user_query: str) -> str:
        if df.empty:
            return 'text'

        column_info = ", ".join([f"{col} ({str(dtype)})" for col, dtype in df.dtypes.items()])
        prompt = (
            f"Data columns: {column_info}\n"
            f"User query: '{user_query}'\n"
            "Suggest output type: 'text', 'table', or 'plot'."
        )

        response = self.llm.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a visualization output expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.2,
            top_p=1.0
        )
        output_type = response.choices[0].message.content.strip().lower()
        return output_type if output_type in ['text', 'table', 'plot'] else 'text'

    def generate_chart(self, df: pd.DataFrame, chart_type='bar'):
        import plotly.express as px
        numeric = df.select_dtypes(include='number').columns.tolist()
        categoric = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime = df.select_dtypes(include='datetime').columns.tolist()

        try:
            if chart_type == 'line' and datetime and numeric:
                return px.line(df.sort_values(datetime[0]), x=datetime[0], y=numeric[0])
            elif chart_type == 'bar' and categoric and numeric:
                return px.bar(df, x=categoric[0], y=numeric[0])
            elif chart_type == 'scatter' and len(numeric) >= 2:
                return px.scatter(df, x=numeric[0], y=numeric[1])
            elif chart_type == 'histogram' and numeric:
                return px.histogram(df, x=numeric[0])
            elif chart_type == 'pie' and categoric and numeric:
                return px.pie(df, names=categoric[0], values=numeric[0])
        except Exception as e:
            print(f"⚠️ Plot generation error: {e}")

        return None

# -------------------------------------------------------------------------
# LLMChatBot
# -------------------------------------------------------------------------
class LLMChatBot:
    def __init__(self):
        self.query_generator = SQLQueryGenerator()
        self.db_handler = DatabaseHandler()
        self.table_schemas = DBConstant.db_schema
        self.chat_history = []

    def run(self, user_input: str) -> Tuple[str, Union[pd.DataFrame, dict]]:
        prompt = f"""
        Determine if this input is a greeting or a question:
        "{user_input}"
        Respond with GREETING or QUESTION only.
        """

        response = self.query_generator.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a user input classifier."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
            temperature=0.0,
            top_p=1.0
        )

        classification = response.choices[0].message.content.strip().upper()

        if classification == "GREETING":
            return "N/A", {"message": "Hello! How can I assist you today?"}

        sql_query = self.query_generator.generate_sql_query(user_input, self.table_schemas)
        if not sql_query:
            return "N/A", {"message": "Sorry, could not generate a valid SQL for your query."}

        result = self.db_handler.execute_query(sql_query)
        return sql_query, result

# -------------------------------------------------------------------------
# main()
# -------------------------------------------------------------------------
def main():
    bot = LLMChatBot()
    visualization = VisualizationEngine()
    print("Text-to-SQL Chatbot (Type 'exit' to quit)\n")

    while True:
        user_input = input("Enter your natural language query: ").strip()

        if user_input.lower() == 'exit':
            print("Exiting...")
            break

        sql_query, result = bot.run(user_input)

        if sql_query == 'N/A' or result is None:
            if isinstance(result, dict) and "message" in result:
                print(f"\n{result['message']}\n")
            else:
                print("\n⚠️ Could not process the input.\n")
            continue

        if isinstance(result, dict):
            if "error" in result:
                print("\n❌ Error:", result["error"])
            elif "message" in result:
                print(f"\n{result['message']}\n")
            continue

        if isinstance(result, pd.DataFrame):
            clean_result = remove_sensitive_columns(result)
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

# -------------------------------------------------------------------------
# Run
# -------------------------------------------------------------------------
if __name__ == '__main__':
    main()
