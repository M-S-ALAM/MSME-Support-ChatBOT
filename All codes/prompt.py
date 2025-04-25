import os
import re
import pandas as pd
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from tabulate import tabulate
from modular_code.config import ChatGPTConfig
from modular_code.models.database import DynamicDatabase


# class SQLQueryGenerator:
#     def __init__(self, api_key):
#         self.client = OpenAI(api_key=api_key)

#     def generate_sql_query(self, natural_language_query, table_schemas):
#         schema_info = "\n".join([f"Table {name}: {schema}" for name, schema in table_schemas.items()])
#         prompt = f"""
#         You are an expert in SQL and use only MySQL-compatible syntax.

#         - In MySQL, the DATEDIFF function returns the number of days between two dates.
#         - Do NOT use DATEDIFF with a unit like 'month'. Instead, calculate the number of months by dividing the days by 30 or use TIMESTAMPDIFF if needed.
#         - If the query cannot be answered based on the schema, respond with "NO_SQL".

#         Table Schemas:
#         {schema_info}

#         Natural Language Query:
#         {natural_language_query}

#         SQL Query:
#         """

#         response = self.client.chat.completions.create(
#             model="gpt-4-turbo",
#             messages=[
#                 {"role": "system", "content": "You are an SQL query generator."},
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=300,
#             temperature=0.3,
#             top_p=1.0
#         )

#         sql_query = response.choices[0].message.content.strip()
#         return self.clean_sql_query(sql_query)

#     @staticmethod
#     def clean_sql_query(query):
#         match = re.search(r"```sql\s*(.*?)\s*```", query, re.DOTALL)
#         cleaned_query = match.group(1).strip() if match else query.strip()

#         # Handle non-SQL responses
#         if "no_sql" in cleaned_query.lower() or not re.match(r"^(SELECT|WITH|INSERT|UPDATE|DELETE|SHOW)", cleaned_query, re.IGNORECASE):
#             return None
#         return cleaned_query


class DatabaseHandler:
    def __init__(self):
        self.db_instance = DynamicDatabase()
        self.db_instance.connect()
        self.engine = self.db_instance.engine

    def execute_query(self, query):
        if query is None:
            return {"error": "❌ The requested information does not exist in the database schema."}

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(sql=text(query), con=conn)
            return df

        except SQLAlchemyError as e:
            error_msg = str(e.__cause__ or e)
            if "doesn't exist" in error_msg.lower() or "unknown column" in error_msg.lower():
                return {"error": "❌ The SQL query references tables or columns not present in the database schema."}
            else:
                return {"error": f"❌ SQL execution error: {error_msg}"}

        except Exception as e:
            return {"error": f"❌ Unexpected error: {str(e)}"}


class LLMChatBot:
    def __init__(self):
        self.table_schemas = {
            "Customer": "customer_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, company_name VARCHAR(255) NOT NULL, sector ENUM('Manufacturing', 'Metal Fabrication', 'Automotive', 'Construction', 'Machinery', 'Electronics', 'Plastics', 'Woodworking', 'Textiles', 'Food Processing', 'Packaging', 'Chemical', 'Aerospace', 'Medical Devices') NOT NULL DEFAULT Manufacturing",
            "Department": "department_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, department_name VARCHAR(255) NOT NULL, budget FLOAT NOT NULL, location VARCHAR(255) NOT NULL, manager_id INT",
            "Employee": "employee_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, employee_name VARCHAR(255) NOT NULL, employee_position VARCHAR(255), department_id INT",
            "Invoice": "invoice_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, invoice_number VARCHAR(50) NOT NULL, customer_id INT NOT NULL, project_id INT NOT NULL, amount FLOAT NOT NULL, tax_amount FLOAT NOT NULL DEFAULT 0.0, total_amount FLOAT NOT NULL, issue_date DATE NOT NULL, due_date DATE NOT NULL, status ENUM('DRAFT', 'SENT', 'PAID', 'OVERDUE', 'CANCELLED') NOT NULL DEFAULT InvoiceStatus.DRAFT, notes TEXT",
            "Payment": "payment_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, invoice_id INT NOT NULL, amount FLOAT NOT NULL, payment_date DATE NOT NULL, payment_method ENUM('CREDIT_CARD', 'BANK_TRANSFER', 'CHECK', 'CASH', 'PAYPAL', 'OTHER') NOT NULL, transaction_id VARCHAR(255), notes TEXT",
            "Projects": "project_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, project_name VARCHAR(255) NOT NULL, customer_id INT NOT NULL, employee_id INT NOT NULL, start_of_project DATE NOT NULL, end_of_project DATE NOT NULL",
            "Task": "task_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, title VARCHAR(255) NOT NULL, description TEXT, project_id INT NOT NULL, assigned_to INT, created_by INT NOT NULL, status ENUM('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'ON_HOLD') NOT NULL DEFAULT TaskStatus.NOT_STARTED, priority ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT TaskPriority.MEDIUM, due_date DATE, estimated_hours FLOAT, actual_hours FLOAT, created_at TIMESTAMP, updated_at TIMESTAMP",
            "TimeEntry": "time_entry_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, employee_id INT NOT NULL, project_id INT NOT NULL, task_id INT, date DATE NOT NULL, hours FLOAT NOT NULL, description TEXT, billable BOOLEAN NOT NULL DEFAULT True, approved BOOLEAN NOT NULL DEFAULT False"
        }
        # self.table_schemas = {
        #     "Employee": "employee_id INT, employee_name VARCHAR(100), employee_position VARCHAR(100)",
        #     "Customer": "customer_id INT, company_name VARCHAR(100), sector VARCHAR(100)",
        #     "Projects": "project_id INT, project_name VARCHAR(100), start_of_project DATE, end_of_project DATE, customer_id INT, employee_id INT"
        # }
        self.query_generator = SQLQueryGenerator(api_key=ChatGPTConfig.API_KEY)
        self.db_handler = DatabaseHandler()

    def run(self, user_input):
        sql_query = self.query_generator.generate_sql_query(user_input, self.table_schemas)
        result = self.db_handler.execute_query(sql_query)
        return sql_query or "N/A (non-SQL response)", result


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
        elif isinstance(result, pd.DataFrame) and result.empty:
            print("\nNo results found.")
        elif isinstance(result, pd.DataFrame):
            print("\nQuery Result:\n", tabulate(result, headers='keys', tablefmt="pretty"), "\n")
        else:
            print("\n⚠️ Unexpected response format.\n")


if __name__ == '__main__':
    main()
