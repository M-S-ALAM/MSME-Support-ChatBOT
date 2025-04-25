from langchain.chat_models import ChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_experimental.sql import SQLDatabaseChain
from sqlalchemy import create_engine
from modular_code.config import ChatGPTConfig


class Chatbot:
    def __init__(self, database_url, openai_api_key):
        self.database_url = database_url
        self.openai_api_key = openai_api_key
        self.db = self._initialize_database()
        self.llm = self._initialize_openai()
        self.agent_executor = self._create_agent_executor()

    def _initialize_database(self):
        """Initialize the database connection."""
        try:
            engine = create_engine(self.database_url)
            db = SQLDatabase(engine)
            return db
        except Exception as e:
            print("Error: Could not connect to the database.")
            print(f"Details: {e}")
            exit(1)

    def _initialize_openai(self):
        """Initialize the OpenAI LLM."""
        try:
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",  # Use "gpt-4" if you have access
                temperature=0,
                openai_api_key=self.openai_api_key,
                max_tokens=512,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                n=1,
                stop=None,
                verbose=True,
                request_timeout=60,
            )
            return llm
        except Exception as e:
            print("Error: Could not initialize the OpenAI model.")
            print(f"Details: {e}")
            exit(1)

    def _create_agent_executor(self):
        """Create the LangChain agent executor."""
        return create_sql_agent(self.llm, db=self.db, agent_type="openai-tools", verbose=True)

    def start_chat(self):
        """Start the chatbot interaction."""
        print("Welcome to the LangChain Chatbot! Type 'exit' to quit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            try:
                response = self.agent_executor.invoke(user_input)
                print("Bot:", response['output'])
            except Exception as e:
                print("Bot: Sorry, I couldn't process your request.")
                print(f"Error: {e}")


if __name__ == "__main__":
    DATABASE_URL = "mysql+pymysql://shobot:shobot@localhost/walmart_chatbot_dummy"
    chatbot_instance = Chatbot(DATABASE_URL, ChatGPTConfig.API_KEY)
    chatbot_instance.start_chat()
