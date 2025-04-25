from langchain.chat_models import ChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from sqlalchemy import create_engine
from modular_code.config import ChatGPTConfig
from langgraph.graph import StateGraph, END
from typing import Dict, Any
import streamlit as st
import pandas as pd
import plotly.express as px

class Chatbot:
    def __init__(self, database_url, openai_api_key):
        self.database_url = database_url
        self.openai_api_key = openai_api_key
        self.db = self._initialize_database()
        self.llm = self._initialize_openai()
        self.agent_executor = self._create_agent_executor()
        self.graph = self._create_langgraph()

    def _initialize_database(self):
        try:
            engine = create_engine(self.database_url)
            db = SQLDatabase(engine)
            return db
        except Exception as e:
            st.error("Error: Could not connect to the database.")
            st.error(f"Details: {e}")
            exit(1)

    def _initialize_openai(self):
        try:
            llm = ChatOpenAI(
                model="gpt-4o",
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
            st.error("Error: Could not initialize the OpenAI model.")
            st.error(f"Details: {e}")
            exit(1)

    def _create_agent_executor(self):
        return create_sql_agent(self.llm, db=self.db, agent_type="openai-tools", verbose=True)

    def query_generation(self, state: Dict[str, Any]):
        user_input = state["input"]
        response = self.agent_executor.invoke(user_input)
        state["sql_query"] = response.get('intermediate_steps', [])[0][0].log if response.get('intermediate_steps') else ""
        state["db_response"] = response['output']
        return state

    def fetch_data(self, state: Dict[str, Any]):
        query = state.get("sql_query", "").strip()
        if not query:
            raise ValueError("No SQL query was generated to fetch data.")

        df = pd.read_sql(query, self.db._engine)
        state["data"] = df
        return state

    def determine_visualization(self, state: Dict[str, Any]):
        df = state["data"]
        prompt = f"Given the dataframe columns: {df.columns.tolist()} and the query: '{state['input']}', suggest the best visualization type from ['line', 'bar', 'scatter', 'histogram', 'pie']."
        response = self.llm.predict(prompt)
        vis_type = response.lower().strip()
        state["visualization"] = vis_type if vis_type in ['line', 'bar', 'scatter', 'histogram', 'pie'] else 'table'
        return state

    def generate_llm_response(self, state: Dict[str, Any]):
        prompt = (
            f"The user asked: '{state['input']}'. The database provided the data. Suggest a concise insight or summary for this data."
        )
        response = self.llm.predict(prompt)
        state["final_response"] = response
        return state

    def _create_langgraph(self):
        graph = StateGraph(Dict[str, Any])

        graph.add_node("query_generation", self.query_generation)
        graph.add_node("fetch_data", self.fetch_data)
        graph.add_node("determine_visualization", self.determine_visualization)
        graph.add_node("generate_llm_response", self.generate_llm_response)

        graph.set_entry_point("query_generation")
        graph.add_edge("query_generation", "fetch_data")
        graph.add_edge("fetch_data", "determine_visualization")
        graph.add_edge("determine_visualization", "generate_llm_response")
        graph.add_edge("generate_llm_response", END)

        return graph.compile()

    def visualize_data(self, df, vis_type):
        if vis_type == 'line':
            fig = px.line(df, title="Line Chart")
        elif vis_type == 'bar':
            fig = px.bar(df, title="Bar Chart")
        elif vis_type == 'scatter':
            fig = px.scatter(df, title="Scatter Plot")
        elif vis_type == 'histogram':
            fig = px.histogram(df, title="Histogram")
        elif vis_type == 'pie' and df.shape[1] >= 2:
            fig = px.pie(df, names=df.columns[0], values=df.columns[1], title="Pie Chart")
        else:
            st.dataframe(df)
            return
        st.plotly_chart(fig)

    def start_chat(self):
        st.title("💬 Walmart MSME ChatBOT")
        user_input = st.text_input("Ask your MSME database query:")

        if user_input:
            with st.spinner("Processing..."):
                result = self.graph.invoke({"input": user_input})
                st.subheader("Generated SQL Query")
                st.code(result["sql_query"], language="sql")
                st.subheader("LLM Response")
                st.write(result["final_response"])
                st.subheader("Visualization")
                self.visualize_data(result["data"], result["visualization"])


if __name__ == "__main__":
    DATABASE_URL = "mysql+pymysql://shobot:shobot@localhost/walmart_chatbot_dummy"
    chatbot_instance = Chatbot(DATABASE_URL, ChatGPTConfig.API_KEY)
    chatbot_instance.start_chat()