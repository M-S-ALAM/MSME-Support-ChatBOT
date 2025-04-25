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

# Enable imports from parent directory (modular_code)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modular_code.utils.constant import (
    DbSqlAlchemy,
    History_Approach,
    UI_constants,
    DBConstant,
    OpenAIConfig
)
from sql_query_generation import SQLQueryGenerator
from modular_code.models.database import DynamicDatabase

# -------------------------------------------------------------------------
# Singleton Class: Manages a persistent SQLite database connection
# -------------------------------------------------------------------------
class DynamicDatabase:
    """Singleton class to manage database engine for SQLite."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initializes the engine path for the SQLite DB."""
        if self._initialized:
            return
        self.engine = None
        self.db_path = 'Database/manufacturing_projects.db'
        self._initialized = True

    def connect(self):
        """Creates a SQLAlchemy engine if not already initialized."""
        if not self.engine:
            self.engine = create_engine(f'sqlite:///{self.db_path}')

    def get_engine(self):
        """Returns the SQLAlchemy engine instance."""
        if not self.engine:
            self.connect()
        return self.engine


# -------------------------------------------------------------------------
# Class: Executes SQL queries using SQLAlchemy
# -------------------------------------------------------------------------
class DatabaseHandler:
    """Handles execution of SQL queries via SQLAlchemy."""

    def __init__(self):
        """Initializes the database engine."""
        self.db_instance = DynamicDatabase()
        self.engine = self.db_instance.get_engine()

    def execute_query(self, query):
        """
        Executes SQL and returns result as DataFrame or message.

        Args:
            query (str): SQL query to execute.

        Returns:
            pd.DataFrame | dict: Result or error/message dict.
        """
        if query is None:
            return {"message": "The requested information does not exist in the database schema."}

        try:
            df = pd.read_sql(sql=text(query), con=self.engine)
            return df
        except SQLAlchemyError:
            return {"message": "Sorry, this question cannot be answered with the information currently in the Database."}
        except Exception as e:
            return {"error": f"❌ Unexpected error: {str(e)}"}


# -------------------------------------------------------------------------
# Class: Chatbot that classifies input, generates SQL, and fetches results
# -------------------------------------------------------------------------
class LLMChatBot:
    """Main chatbot logic for handling input, classification, and querying."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LLMChatBot, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes LLM, query generator, database handler."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self.table_schemas = DBConstant.db_schema
        self.db_name = DBConstant.db_name
        self.db_type = DBConstant.db_type
        self.chat_history = []
        self.query_generator = SQLQueryGenerator()
        self.db_handler = DatabaseHandler()

    def run(self, user_input):
        """
        Classifies user input and runs corresponding SQL or reply.

        Args:
            user_input (str): Natural language input from the user.

        Returns:
            Tuple[str, Union[pd.DataFrame, dict]]: SQL query and result.
        """
        # Prompt OpenAI to classify input as greeting or question
        prompt = f"""
        You are a helpful assistant. Determine if the following input is a greeting or a valid question:
        Input: "{user_input}"
        Respond with "GREETING" if it is a greeting (e.g., "hi", "hello", "hey"), or "QUESTION" if it is a valid question.
        """

        response = self.query_generator.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "If the user says 'hi', 'hello', or similar greetings, respond with 'How can I help you?'."
                },
                {"role": "system", "content": "You are a classifier for user inputs."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=OpenAIConfig.OpenAI_max_tokens,
            temperature=OpenAIConfig.OpenAI_temperature,
            top_p=OpenAIConfig.OpenAI_top_p
        )

        classification = response.choices[0].message.content.strip().upper()
        print(classification)

        self.chat_history.extend([
            {"role": "user", "content": user_input},
        ])

        # Keep only the last 10 messages in chat history
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]

        # Reply to greeting
        if classification == "GREETING":
            return "N/A", {"message": "Hello! How can I assist you today?"}

        # Generate SQL and fetch result
        sql_query = self.query_generator.generate_sql_query(user_input, self.table_schemas)

        if not sql_query:
            return "N/A", {"message": "Sorry, this question cannot be answered with the information currently in the Database."}

        result = self.db_handler.execute_query(sql_query)
        return sql_query, result


# -------------------------------------------------------------------------
# CLI Entry Point
# -------------------------------------------------------------------------
def main():
    """Entry point for running the chatbot in a CLI loop."""
    bot = LLMChatBot()
    print("Text-to-SQL Generator (Type 'exit' to quit)\n")

    while True:
        user_input = input("Enter your natural language query: ").strip()

        if user_input.lower() == 'exit':
            print("Exiting...")
            break

        sql_query, result = bot.run(user_input)

        if sql_query != 'N/A':
            print("\nSQL Query:\n", sql_query)

        # Display result
        if isinstance(result, dict) and "error" in result:
            print("\n❌ Error:", result["error"])
        elif isinstance(result, dict) and "message" in result:
            print(f"\n{result['message']}\n")
        elif isinstance(result, pd.DataFrame) and not result.empty:
            print("\nQuery Result:\n", tabulate(result, headers='keys', tablefmt="pretty"), "\n")
        else:
            print("\nNo results found or unexpected response format.\n")


if __name__ == '__main__':
    main()
