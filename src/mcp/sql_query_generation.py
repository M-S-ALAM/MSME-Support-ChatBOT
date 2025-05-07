"""
This module generates SQL queries from natural language using an LLM client (default: OpenAI's GPT-4).
It takes a natural language query and a dictionary of table schemas as input,
and returns the corresponding SQL query.
MCP Format: Modular, Configurable, Pluggable.
"""
import re
import logging
from openai import OpenAI, OpenAIError
from src.utils.constant import OpenAIConfig, Constants, DbSqlAlchemyConstant

class SQLQueryGenerator:
    """
    Modular, Configurable, Pluggable SQL Query Generator.
    """

    def __init__(
        self,
        llm_client=None,
        config=None,
        logger=None,
        chat_history=None,
    ):
        """
        Args:
            llm_client: LLM client instance (default: OpenAI with API key from config)
            config: Configuration object (default: OpenAIConfig)
            logger: Logger instance (default: module logger)
            chat_history: Optional initial chat history (default: empty list)
        """
        self.config = config or OpenAIConfig
        self.client = llm_client or OpenAI(api_key=self.config.OpenAI_API_KEY)
        self.db_chat_history = chat_history if chat_history is not None else []
        self.logger = logger or self._default_logger()
        self.logger.info("SQLQueryGenerator initialized with MCP format.")

    def _default_logger(self):
        logging.basicConfig(
            level=Constants.LOG_LEVEL,
            format=Constants.LOG_FORMAT,
            handlers=[
                logging.FileHandler(f"{Constants.LOG_PATH}/sql_query_generator"),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logging.getLogger("httpx").disabled = True
        return logger

    def generate_sql_query(self, natural_language_query, table_schemas):
        """
        Generate an SQL query from a natural language query and table schemas.

        Args:
            natural_language_query (str): The user's question.
            table_schemas (dict): Mapping of table names to schema strings.

        Returns:
            str or None: The generated SQL query, or None if not answerable.
        """
        schema_info = "\n".join([f"Table {name}: {schema}" for name, schema in table_schemas.items()])
        prompt = self._build_prompt(natural_language_query, schema_info)
        self.logger.info(f"Natural Language Query: {natural_language_query}")
        try:
            response = self.client.chat.completions.create(
                model=self.config.OpenAI_model,
                messages=self._build_messages(prompt),
                max_tokens=self.config.OpenAI_max_tokens,
                temperature=self.config.OpenAI_temperature,
                top_p=self.config.OpenAI_top_p,
                frequency_penalty=self.config.OpenAI_frequency_penalty,
            )
            result_response = self.clean_sql_query(response.choices[0].message.content.strip())
            self.logger.info(f"Generated SQL Query: {result_response}")
            self._update_history(prompt)
            return result_response
        except OpenAIError as e:
            print(f"OpenAI API Error: {str(e)}")
            self.logger.error(f"OpenAI API Error: {str(e)}")
            return None
        except Exception as ex:
            print(f"Unexpected Error: {str(ex)}")
            self.logger.error(f"Unexpected Error: {str(ex)}")
            return None

    def _build_prompt(self, natural_language_query, schema_info):
        """
        Build the prompt for the LLM.
        """
        return (
            f"You are an expert in SQL and use only {DbSqlAlchemyConstant.db_type} syntax.\n"
            "- If the query cannot be answered based on the schema, respond with \"NO_SQL\".\n"
            f"Table Schemas:\n{schema_info}\n\n"
            f"Natural Language Query:\n{natural_language_query}\n\n"
            "SQL Query:\n"
        )

    def _build_messages(self, prompt):
        """
        Build the message list for the LLM client.
        """
        return [
            {
                "role": "system",
                "content": (
                    "You are a professional SQL query generator. Use the user's input and schema context to generate a correct SQL query. "
                    f"Use the following previous query history to maintain context:\n{self.db_chat_history}"
                )
            },
            {
                "role": "system",
                "content": (
                    "Ensure queries follow these steps:\n"
                    "1. Understand the intent (SELECT/UPDATE/etc.)\n"
                    "2. Match fields/tables from schema\n"
                    "3. Resolve vague references and homophones\n"
                    "4. Validate SQL syntax\n"
                    "5. Return SQL or 'NO_SQL' if not answerable"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

    def _update_history(self, prompt):
        """
        Update the chat history for context.
        """
        self.db_chat_history.extend([
            {"role": "user", "content": prompt},
        ])
        if len(self.db_chat_history) > 10:
            self.db_chat_history = self.db_chat_history[-10:]

    @staticmethod
    def clean_sql_query(query):
        """
        Clean the LLM output to extract the SQL query.
        """
        match = re.search(r"```sql\s*(.*?)\s*```", query, re.DOTALL)
        cleaned_query = match.group(1).strip() if match else query.strip()
        if "no_sql" in cleaned_query.lower() or not re.match(r"^(SELECT|WITH|INSERT|UPDATE|DELETE|SHOW)", cleaned_query, re.IGNORECASE):
            return None
        return cleaned_query


