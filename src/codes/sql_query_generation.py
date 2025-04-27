"""
This module generates SQL queries from natural language using OpenAI's GPT-4 model.
It takes a natural language query and a dictionary of table schemas as input,
and returns the corresponding SQL query.
"""
import re
import logging
from openai import OpenAI, OpenAIError  # Ensure OpenAIError is imported
from src.utils.constant import OpenAIConfig, Constants, DbSqlAlchemyConstant

logging.basicConfig(level=Constants.LOG_LEVEL,
                    format=Constants.LOG_FORMAT,
                    handlers=[
                    logging.FileHandler("{}/sql_query_generator".format(Constants.LOG_PATH)),
                    logging.StreamHandler()]
    )

LOGGER = logging.getLogger(__name__)
logging.getLogger("httpx").disabled = True

class SQLQueryGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=OpenAIConfig.OpenAI_API_KEY)
        self.db_chat_history = []
        LOGGER.info("SQLQueryGenerator initialized with OpenAI API key.")

    def generate_sql_query(self, natural_language_query, table_schemas):
        schema_info = "\n".join([f"Table {name}: {schema}" for name, schema in table_schemas.items()])
        prompt = f"""
        You are an expert in SQL and use only {DbSqlAlchemyConstant.db_type} syntax.
        - If the query cannot be answered based on the schema, respond with "NO_SQL".
        Table Schemas:
        {schema_info}

        Natural Language Query:
        {natural_language_query}

        SQL Query:
        """
        LOGGER.info(f"Natural Language Query: {natural_language_query}")
        try:
            response = self.client.chat.completions.create(
                model=OpenAIConfig.OpenAI_model,
                messages=[
                    {
                "role": "system",
                "content": (
                    f"You are a professional SQL query generator. Use the user's input and schema context to generate a correct SQL query. "
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
            }],
            max_tokens=OpenAIConfig.OpenAI_max_tokens,
                temperature=OpenAIConfig.OpenAI_temperature,
                top_p=OpenAIConfig.OpenAI_top_p,
                frequency_penalty=OpenAIConfig.OpenAI_frequency_penalty,
            )

            result_response = self.clean_sql_query(response.choices[0].message.content.strip())
            LOGGER.info(f"Generated SQL Query: {result_response}")
            self.db_chat_history.extend([
                {"role": "user", "content": prompt},
            ])
        

            if len(self.db_chat_history) > 10:
                self.db_chat_history = self.db_chat_history[-10:]

            return result_response

        except OpenAIError as e:
            print(f"OpenAI API Error: {str(e)}")
            LOGGER.error(f"OpenAI API Error: {str(e)}")
            return None

        except Exception as ex:
            print(f"Unexpected Error: {str(ex)}")
            LOGGER.error(f"Unexpected Error: {str(ex)}")    
            return None

    @staticmethod
    def clean_sql_query(query):
        match = re.search(r"```sql\s*(.*?)\s*```", query, re.DOTALL)
        cleaned_query = match.group(1).strip() if match else query.strip()
        if "no_sql" in cleaned_query.lower() or not re.match(r"^(SELECT|WITH|INSERT|UPDATE|DELETE|SHOW)", cleaned_query, re.IGNORECASE):
            return None
        return cleaned_query
