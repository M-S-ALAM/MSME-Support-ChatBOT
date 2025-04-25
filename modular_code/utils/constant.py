"""
File contain all the constants used in the project
===========================================================
"""
import os
from dotenv import load_dotenv

from modular_code.config import DbSqlAlchemy

# Load environment variables from a .env file
load_dotenv()

__authors__ = ['shahbazalam@gyandata.com']

class DbSqlAlchemyConstant:
    db_type = os.getenv("DB_TYPE")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT", "3306")
    db_path = os.getenv("DB_PATH")
    sqlite_db_name = os.getenv("SQLITE_DB_NAME")

class DBConstant:
    db_schema = {
            "Customer": "customer_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, company_name VARCHAR(255) NOT NULL, sector ENUM('Manufacturing', 'Metal Fabrication', 'Automotive', 'Construction', 'Machinery', 'Electronics', 'Plastics', 'Woodworking', 'Textiles', 'Food Processing', 'Packaging', 'Chemical', 'Aerospace', 'Medical Devices') NOT NULL DEFAULT Manufacturing",
            "Department": "department_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, department_name VARCHAR(255) NOT NULL, budget FLOAT NOT NULL, location VARCHAR(255) NOT NULL, manager_id INT",
            "Employee": "employee_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, employee_name VARCHAR(255) NOT NULL, employee_position VARCHAR(255), department_id INT",
            "Invoice": "invoice_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, invoice_number VARCHAR(50) NOT NULL, customer_id INT NOT NULL, project_id INT NOT NULL, amount FLOAT NOT NULL, tax_amount FLOAT NOT NULL DEFAULT 0.0, total_amount FLOAT NOT NULL, issue_date DATE NOT NULL, due_date DATE NOT NULL, status ENUM('DRAFT', 'SENT', 'PAID', 'OVERDUE', 'CANCELLED') NOT NULL DEFAULT InvoiceStatus.DRAFT, notes TEXT",
            "Payment": "payment_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, invoice_id INT NOT NULL, amount FLOAT NOT NULL, payment_date DATE NOT NULL, payment_method ENUM('CREDIT_CARD', 'BANK_TRANSFER', 'CHECK', 'CASH', 'PAYPAL', 'OTHER') NOT NULL, transaction_id VARCHAR(255), notes TEXT",
            "Projects": "project_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, project_name VARCHAR(255) NOT NULL, customer_id INT NOT NULL, employee_id INT NOT NULL, start_of_project DATE NOT NULL, end_of_project DATE NOT NULL",
            "Task": "task_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, title VARCHAR(255) NOT NULL, description TEXT, project_id INT NOT NULL, assigned_to INT, created_by INT NOT NULL, status ENUM('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'ON_HOLD') NOT NULL DEFAULT TaskStatus.NOT_STARTED, priority ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT TaskPriority.MEDIUM, due_date DATE, estimated_hours FLOAT, actual_hours FLOAT, created_at TIMESTAMP, updated_at TIMESTAMP",
            "TimeEntry": "time_entry_id INT PRIMARY KEY AUTOINCREMENT NOT NULL, employee_id INT NOT NULL, project_id INT NOT NULL, task_id INT, date DATE NOT NULL, hours FLOAT NOT NULL, description TEXT, billable BOOLEAN NOT NULL DEFAULT True, approved BOOLEAN NOT NULL DEFAULT False"
        }
    db_name = os.getenv("DB_NAME")
    db_type = os.getenv("DB_TYPE")

class Constants:
    """
    Class to hold all the constants used in the project
    """

    # Constants for file paths
    DATA_PATH = "Database/"
    OUTPUT_PATH = "output/"
    LOG_PATH = "logs/"

    # Constants for model parameters
    MODEL_NAME = "my_model"
    LEARNING_RATE = 0.001
    BATCH_SIZE = 32

    # Constants for training parameters
    EPOCHS = 10
    VALIDATION_SPLIT = 0.2

    # Constants for logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # Constants for database connection
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "my_database"
    DB_USER = "my_user"
    DB_PASSWORD = "my_password"
    DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # Constants for API keys        


class OpenAIConfig:
    """
    Class to hold all the constants used in the project
    """
    OpenAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-default-chatgpt-key")
    OpenAI_API_BASE = "https://api.openai.com/v1"
    OpenAI_API_VERSION = "v1"
    # Constants for API keys
    OpenAI_model = "gpt-3.5-turbo"
    OpenAI_max_tokens = 200
    OpenAI_temperature = 0.7
    OpenAI_top_p = 1.0
    OpenAI_frequency_penalty = 0.0
    OpenAI_presence_penalty = 0.0
    OpenAI_n = 1
    OpenAI_stop = None
    OpenAI_timeout = 60


class History_Approach:
    """
    Class to hold all the constants used in the project
    """
    # Constants for history approach
    HISTORY_APPROACH = "history_approach"
    HISTORY_SIZE = 10
    HISTORY_TYPE = "list"
    HISTORY_FILE = "history.json"
    HISTORY_FILE_PATH = "history/"  



class UI_constants:
    """
    Class to hold all the constants used in the project
    """
    # Constants for UI
    UI_TITLE = ":red[💬 Intelligent Chatbot for MSMEs]"
    UI_SUBTITLE = "Chatbot for MSMEs"
    UI_DESCRIPTION = "This is a chatbot for MSMEs"
    UI_BUTTON_TEXT = "Submit"
    UI_BUTTON_COLOR = "#4CAF50"  # Green
    UI_BUTTON_HOVER_COLOR = "#3e8e41"  # Darker green
    UI_BUTTON_TEXT_COLOR = "#FFFFFF"  # White
    UI_BUTTON_BORDER_RADIUS = "5px"
    UI_BUTTON_FONT_SIZE = "16px"            





