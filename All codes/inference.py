import os
import re
import pandas as pd
from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from tabulate import tabulate
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modular_code.utils.constant import ChatGPTConfig, DbSqlAlchemy, History_Approach, UI_constants, DBConstant
from modular_code.utils.prompt import SQLQueryGenerator

from modular_code.models.database import DynamicDatabase
class DynamicDatabase:
    _instance = None  # Singleton pattern

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.engine = None
        self.db_path = 'Database/manufacturing_projects.db'  # Path to your SQLite database
        self._initialized = True

    def connect(self):
        if not self.engine:
            self.engine = create_engine(f'sqlite:///{self.db_path}')

    def get_engine(self):
        if not self.engine:
            self.connect()
        return self.engine



class DatabaseHandler:
    def __init__(self):
        self.db_instance = DynamicDatabase()
        self.engine = self.db_instance.get_engine()

    def execute_query(self, query):
        if query is None:
            return {"message": "The requested information does not exist in the database schema."}

        try:
            df = pd.read_sql(sql=text(query), con=self.engine)
            return df
        except SQLAlchemyError as e:
            error_msg = str(e.__cause__ or e)
            return {"message": "Sorry, this question cannot be answered with the information currently in the Database."}
        except Exception as e:
            return {"error": f"❌ Unexpected error: {str(e)}"}

class LLMChatBot:
    def __init__(self):
        self.table_schemas = DBConstant.table_schemas
        self.db_name = DBConstant.db_name
        self.db_type = DBConstant.db_type

        self.query_generator = SQLQueryGenerator(api_key=ChatGPTConfig.API_KEY)
        self.db_handler = DatabaseHandler()

    def run(self, user_input):
        prompt = f"""
                You are a helpful assistant. Determine if the following input is a greeting or a valid question:
                Input: "{user_input}"
                Respond with "GREETING" if it is a greeting (e.g., "hi", "hello", "hey"), or "QUESTION" if it is a valid question.
                """
        response = self.query_generator.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a classifier for user inputs."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
            temperature=0.3,
            top_p=1.0
        )
        classification = response.choices[0].message.content.strip().upper()

        if classification == "GREETING":
            return "N/A", {"message": "Hello! How can I assist you today?"}
        sql_query = self.query_generator.generate_sql_query(user_input, self.table_schemas)
        if not sql_query:
            return "N/A", {"message": "Sorry, this question cannot be answered with the information currently in the Database."}

        result = self.db_handler.execute_query(sql_query)
        return sql_query, result

def main():
    bot = LLMChatBot()
    print("Text-to-SQL Generator (Type 'exit' to quit)\n")
    while True:
        user_input = input("Enter your natural language query: ").strip()
        if user_input.lower() == 'exit':
            print("Exiting...")
            break

        sql_query, result = bot.run(user_input)
        print("\nSQL Query:\n", sql_query)
        if isinstance(result, dict) and "error" in result:
            print("\n❌ Error:", result["error"])
        elif isinstance(result, pd.DataFrame) and not result.empty:
            print("\nQuery Result:\n", tabulate(result, headers='keys', tablefmt="pretty"), "\n")
        else:
            print("\nNo results found or unexpected response format.\n")

if __name__ == '__main__':
    main()
