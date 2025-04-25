# -- coding: UTF-8 --

"""
Configuration settings for API keys and tokens used in the project.
==================================================================
"""

import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

__authors__ = ['shahbazalam@gyandata.com']


class ChatGPTConfig:
    """
    Configuration class for ChatGPT API.
    """
    API_KEY = os.getenv("OPENAI_API_KEY", "your-default-chatgpt-key")


class DbSqlAlchemy:
    db_type = os.getenv("DB_TYPE")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT", "3306")
    db_path = os.getenv("DB_PATH")
    sqlite_db_name = os.getenv("SQLITE_DB_NAME")

    @classmethod
    def get_connection_url(cls):
        """Returns SQLAlchemy database URL with credentials (keep private)."""
        return f"{cls.db_type}+pymysql://{cls.user}:{cls.password}@{cls.host}:{cls.port}/{cls.db_name}"

    @classmethod
    def get_safe_url(cls):
        """Returns DB URL with password hidden (for logging)."""
        return f"{cls.db_type}+pymysql://{cls.user}:****@{cls.host}:{cls.port}/{cls.db_name}"

