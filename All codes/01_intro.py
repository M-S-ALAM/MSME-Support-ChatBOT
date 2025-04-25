import streamlit as st

class Intro:
    def __init__(self):
        self.intro()

    def intro(self):
        st.title(":red[Intelligent MSME ChatBOT]")
        test_type = st.sidebar.selectbox(
            'Select the documentation type',
            ('Project Document', 'Technical Document')
        )
        page_title, page_content = self.get_page_content(test_type)

        st.subheader(page_title)
        st.markdown(page_content, unsafe_allow_html=True)

    def get_page_content(self, test_type):
        if test_type == 'Project Document':
            page_title = ':green[Project Document]'
            page_content = """
            ## Intelligent MSME ChatBOT

            The Intelligent MSME ChatBOT is an innovative conversational AI solution tailored specifically for micro, small, and medium-sized enterprises (MSMEs). It is designed to assist business owners by providing quick access to relevant information from databases, helping them make informed decisions efficiently.

            ### Features and Use Cases

            #### Database Interaction
            - **Details**: Efficiently retrieves and visualizes data from structured databases.
            - **Use Cases**:
              - Generate detailed reports from sales, inventory, and customer data.
              - Perform real-time analytics based on user queries.

            #### Natural Language Processing
            - **Details**: Converts user queries into SQL queries for database retrieval.
            - **Use Cases**:
              - Seamless interpretation of business-related questions.
              - Generate actionable insights from natural language inputs.

            #### Visualization
            - **Details**: Dynamically generates visual representations of data.
            - **Use Cases**:
              - Provide graphs and charts for sales trends.
              - Visualize customer segmentation and inventory management.

            ### How to Use Intelligent MSME ChatBOT
            1. **Enter Query**: Input your business query in natural language.
            2. **Automatic Processing**: The chatbot translates the query to SQL and retrieves data.
            3. **Result Visualization**: Review results presented as visual graphs, charts, or tables.

            """
        elif test_type == 'Technical Document':
            page_title = ':green[Technical Document]'
            page_content = """
            # Intelligent MSME ChatBOT Technical Document

            ## Overview

            Intelligent MSME ChatBOT integrates advanced NLP with database querying techniques to serve MSME needs effectively. It comprises two main modules: NLP-based query conversion and dynamic data visualization.

            ## Workflow

            1. **Natural Language to SQL**
                - **LLM (GPT-4 Turbo)**: Converts natural language queries to SQL.
                - **Technologies**:
                  - GPT-4 Turbo (OpenAI API)
                  - Prompt engineering

            2. **Database Query Execution**
                - **SQLAlchemy & Pandas**: Execute SQL queries and handle database results.
                - **Technologies**:
                  - SQLAlchemy
                  - Pandas

            3. **Dynamic Visualization**
                - **Visualization Tools**: Presents data using interactive visualizations.
                - **Technologies**:
                  - Plotly
                  - Streamlit

            ## Key Technologies and Tools

            | Component                 | Technologies                          | Cost       |
            |---------------------------|---------------------------------------|------------|
            | NLP Query Generation      | GPT-4 Turbo                           | Chargeable |
            | Database Interaction      | SQLAlchemy, Pandas                    | Free       |
            | Dynamic Visualization     | Plotly, Streamlit                     | Free       |

            ## Installation and Usage

            - Ensure all Python dependencies (`streamlit`, `sqlalchemy`, `pandas`, `plotly`, `openai`) are installed.
            ```bash
            pip install streamlit sqlalchemy pandas plotly openai
            ```

            - Run the Streamlit application:
            ```bash
            streamlit run main_app.py
            ```

            ## Notes

            - Designed specifically for MSMEs to simplify data-driven decision making.
            - Make sure you have active credentials for OpenAI GPT API.

            """
        return page_title, page_content


if __name__ == '__main__':
    Intro()
