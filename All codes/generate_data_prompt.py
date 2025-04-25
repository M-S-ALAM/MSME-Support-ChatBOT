"""
Generate the Prompt
================================================

"""
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, DataError
from openai import OpenAI
from tqdm import tqdm
from modular_code.config import ChatGPTConfig
import json
import re
import numpy as np
import pandas as pd
from faker import Faker

class DummyDataGenerator:

    def __init__(self, db_user, db_password, db_host, db_name, openai_api_key):
        """Initialize database connection and OpenAI client."""
        self.engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
        self.client = OpenAI(api_key=openai_api_key)

    def list_tables(self):
        """Fetch all table names from the database."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES;"))
                tables = [row[0] for row in result]
                return tables
        except Exception as e:
            print(f"❌ Error fetching tables: {e}")
            return []

    def get_columns(self, table_name):
        """Fetch column names and types for a given table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"DESCRIBE `{table_name}`;"))
                columns = {row[0]: row[1] for row in result}  # {column_name: data_type}
                return columns
        except Exception as e:
            print(f"❌ Error fetching columns for `{table_name}`: {e}")
            return {}

    def generate_dummy_data(self):
        """Generate and insert dummy data for all tables."""
        tables = self.list_tables()
        if not tables:
            print("❌ No tables found.")
            return

        for table in tqdm(tables):
            columns = self.get_columns(table)
            if not columns:
                continue
            prompt = f"""
            Develop a Python script to generate dummy data formatted as a DataFrame. The generated data should consider potential trends or seasonality. After generating the data, insert the output into a database, iteratively adjusting table name, column names, and column types throughout the script.

# Steps

1. **Analyze Data Requirements**:
   - Identify trends or seasonal patterns that should be reflected in the data.
   - Determine columns with timestamps or temporal relationships that might exhibit trends.

2. **Identify and Define Iterative Columns**:
   - Iteratively define the table name, column names, and their data types.
   - Determine possible ranges or categorical sets for each column.

3. **Generate Data**:
   - Write Python code using `pandas`, `numpy`, or `faker` to generate dummy data.
   - Ensure existing trends or seasonality are reflected in the generated data.
   - Format data as a `pandas` DataFrame.

4. **Insert Data into Database**:
   - Use `SQLAlchemy` or `pymysql` to connect to the database.
   - Configure the database connection using:
     - db_user="shobot"
     - db_password="shobot"
     - db_host="localhost"
     - db_name="walmart_data"
   - Iteratively insert the DataFrame into the specified database table, adjusting the table name as required.

# Output Format

- A Python script with detailed comments on both the data generation and database insertion processes, highlighting the iterative adjustments.
- Sample DataFrame outputs showing the generated dummy data at different iterations.
- Ensure the script is accessible for someone with basic Python knowledge.

# Notes

- Utilize domain knowledge for realistic trends and seasonality.
- Account for edge cases like non-standard column names or unconventional data types.
- Align generated data with any known schema constraints.
- When considering trends and seasonality, use hypothetical historical data scenarios if applicable to refine dummy data generation.
- Ensure database connection details are securely managed in the script.
                    """
            # Construct dynamic prompt
            prompt += f"""Generate python code for dummy data for a MariaDB table.
            Table Name: `{table}`
            Columns:
            """
            for col_name, col_type in columns.items():
                prompt += f"- {col_name}: {col_type}\n"

            prompt += "\nProvide the output of python code in  **DataFrame** and return the dataframe"

            messages = [
                {"role": "system", "content": "You are an AI that generates logical dummy database code for databases."},
                {"role": "user", "content": prompt}
            ]

            # Call OpenAI API
            try:
                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2048,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )

                generated_data = response.choices[0].message.content.strip()
                print(f"🔍 Raw OpenAI Response for `{table}`:\n{generated_data}")

                # Extract Python code from the response
                match = re.search(r"```python(.*?)```", generated_data, re.DOTALL)
                if match:
                    extracted_code = match.group(1).strip()  # Get only the Python code
                else:
                    print(f"❌ No valid Python code detected for `{table}`")
                    extracted_code = None

                if extracted_code:
                    safe_globals = {"pd": pd, "np": np, "faker": Faker}
                    #exec(extracted_code, safe_globals)


            except Exception as e:
                print(f"❌ Error processing `{table}`: {e}")



if __name__ == '__main__':
    generator = DummyDataGenerator(
        db_user="shobot",
        db_password="shobot",
        db_host="localhost",
        db_name="walmart_chatbot_dummy",
        openai_api_key=ChatGPTConfig.API_KEY
    )
    generator.generate_dummy_data()

