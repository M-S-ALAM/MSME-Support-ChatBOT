import streamlit as st
import warnings
import pandas as pd
from openai import OpenAI

from inference import LLMChatBot
from modular_code.config import ChatGPTConfig
from modular_code.utils.constant import UI_constants, OpenAIConfig
from visualization_plot import VisualizationEngine

warnings.filterwarnings('ignore')


class ShoppingChatBot:
    """
    Streamlit-based chatbot that processes user queries, generates SQL,
    fetches results from a database, and visualizes results using Plotly.
    """

    def __init__(self):
        """Initializes the chatbot UI and state, sets up LLM and model selector."""
        st.title(UI_constants.UI_TITLE)

        self.bot = LLMChatBot()
        self.llm_client = OpenAI(api_key=ChatGPTConfig.API_KEY)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        self.init_chat()

    def init_chat(self):
        """
        Renders the chat UI and restores previous messages from session state.
        Waits for new user input to trigger query processing.
        """
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                for content_type, content in message["content"].items():
                    self.render_message_block(content_type, content)

        if prompt := st.chat_input("Query your Database here..."):
            # Clear old state if query changes
            st.session_state.pop('visualization_types', None)
            st.session_state.pop('visualization_df', None)
            st.session_state.pop('user_query', None)
            self.process_user_prompt(prompt)

    def process_user_prompt(self, prompt):
        """
        Processes the user query: generates SQL, fetches results,
        renders results as text, table, or plot.
        """
        st.session_state.messages.append({"role": "user", "content": {"text": prompt}})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🔍 Thinking..."):
                try:
                    sql_query, result = self.bot.run(prompt)
                except Exception as e:
                    st.error(f"❌ Failed to process query: {e}")
                    return

                message_content = {}
                result = self.remove_sensitive_columns(result)

                if isinstance(result, pd.DataFrame):
                    st.session_state['chatbot_df'] = result
                    st.session_state['chat_query'] = prompt
                    st.session_state['visualization_df'] = result
                    st.session_state['user_query'] = prompt

                    if result.shape == (1, 1):
                        val = result.iloc[0, 0]
                        llm_text = self.get_llm_response(prompt, val)
                        message_content["text"] = llm_text
                        st.markdown(llm_text)
                    else:
                        message_content["table"] = result
                        st.dataframe(result)
                        self.render_suggested()

                elif isinstance(result, dict):
                    if "message" in result:
                        message_content["text"] = result["message"]
                        st.markdown(result["message"])
                    elif "error" in result:
                        message_content["error"] = result["error"]
                        st.error(result["error"])
                else:
                    message_content["text"] = "Sorry, this question cannot be answered with the information currently in the Database."
                    st.info(message_content["text"])

                st.session_state.messages.append({"role": "assistant", "content": message_content})

    def render_suggested(self):
        """
        Allows users to preview and persist multiple visualizations by storing selected charts in session state.
        """
        if 'visualization_df' not in st.session_state:
            st.warning("No data available for plotting.")
            return

        df = st.session_state['visualization_df']
        user_query = st.session_state['user_query']
        engine = VisualizationEngine()

        # Generate suggestions if not already in session state
        if 'visualization_types' not in st.session_state:
            suggested_types = engine.suggest_visualization_types(df, user_query)
            st.session_state['visualization_types'] = suggested_types

        suggested_types = st.session_state.get('visualization_types', [])
        if not suggested_types:
            st.markdown("No chart types suggested.")
            return

        # Store shown plots in session
        if 'selected_charts' not in st.session_state:
            st.session_state.selected_charts = []

        # Let user select a chart to add
        selected_chart = st.selectbox("Choose a chart to add below:", options=suggested_types)

        # Add selected chart to list if not already there
        if selected_chart and selected_chart not in st.session_state.selected_charts:
            st.session_state.selected_charts.append(selected_chart)

        # Render all previously selected charts
        st.subheader("📊 Your Selected Visualizations")
        for chart_type in st.session_state.selected_charts:
            fig = engine.generate_chart(df.copy(), chart_type)
            if fig:
                st.markdown(f"### {chart_type.capitalize()} Chart")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Could not generate a {chart_type} chart.")

    def remove_sensitive_columns(self, result):
        """
        Removes sensitive or identifying columns from the result before displaying.

        Args:
            result: DataFrame or list of dicts returned by query.

        Returns:
            Sanitized result with sensitive fields removed.
        """
        columns_to_remove = {
            "customer_id", "employee_id", "project_id",
            "department_id", "invoice_id", "payment_id",
            "task_id", "time_entry_id"
        }

        if isinstance(result, pd.DataFrame):
            return result.drop(columns=[col for col in columns_to_remove if col in result.columns], errors='ignore')
        elif isinstance(result, list) and result and isinstance(result[0], dict):
            return [{k: v for k, v in row.items() if k not in columns_to_remove} for row in result]

        return result

    def get_llm_response(self, query, value):
        """
        Uses the LLM to summarize or interpret single-value query results.

        Args:
            query (str): Original user prompt.
            value (Any): Value to explain.

        Returns:
            str: LLM-generated explanation.
        """
        prompt = f"The user asked: '{query}'. The result from the database is '{value}'. Provide a simple summary."

        try:
            response = self.llm_client.chat.completions.create(
                model=OpenAIConfig.OpenAI_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant providing insights based on database query results."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=OpenAIConfig.OpenAI_max_tokens,
                temperature=OpenAIConfig.OpenAI_temperature,
                top_p=OpenAIConfig.OpenAI_top_p
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Failed to generate insight: {e}"

    def render_message_block(self, content_type, content):
        """
        Renders a stored message (text, table, chart, etc.) from session state.

        Args:
            content_type (str): The type of content ('text', 'sql', 'table', etc.)
            content (Any): The actual content to render.
        """
        if content_type == "text":
            st.markdown(content)
        elif content_type == "sql":
            st.markdown(f"**Generated SQL Query:**\n```sql\n{content}\n```")
        elif content_type == "table" and isinstance(content, pd.DataFrame):
            st.dataframe(content)
        elif content_type == "error":
            st.error(content)
        elif content_type == "image":
            st.plotly_chart(content, use_container_width=True)


if __name__ == "__main__":
    ShoppingChatBot()
