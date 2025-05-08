"""
VisualizationEngine Module
=====================================================================================
VisualizationEngine: A modular and configurable engine for generating data visualizations
and suggesting output types based on user queries and pandas DataFrames.
This class provides a flexible interface for integrating with various LLMs and plotting libraries,  
allowing for easy extension and customization.
"""
import pandas as pd
from openai import OpenAI, OpenAIError
from src.utils.constant import OpenAIConfig
from typing import Optional, List, Any


def remove_sensitive_columns(result):
    columns_to_remove = {
        "customer_id", "employee_id", "project_id", "department_id",
        "invoice_id", "payment_id", "task_id", "time_entry_id"
    }
    if isinstance(result, pd.DataFrame):
        return result.drop(columns=[col for col in columns_to_remove if col in result.columns], errors='ignore')
    elif isinstance(result, list) and result and isinstance(result[0], dict):
        return [{k: v for k, v in row.items() if k not in columns_to_remove} for row in result]
    return result


class VisualizationEngine:
    """
    VisualizationEngine provides a modular, configurable, and pluggable interface for generating
    data visualizations and suggesting output types based on user queries and pandas DataFrames.

    Features:
    - Uses an LLM (default: OpenAI GPT) to suggest the most appropriate output type ('text', 'table', or 'plot')
      for a given DataFrame and user query.
    - Supports automatic chart generation using a pluggable plotting backend (default: plotly.express).
    - Allows injection of custom LLM clients, configuration objects, and supported chart types for flexibility.
    - Designed for easy extension and integration into larger data analysis or chatbot systems.

    Args:
        llm_client: Optional LLM client instance for output type suggestion (default: OpenAI with API key from config).
        config: Optional configuration object for LLM and plotting settings (default: OpenAIConfig).
        supported_types: Optional list of supported chart types (default: ['line', 'bar', 'scatter', 'histogram', 'pie', 'trend']).

    Methods:
        suggest_output_type(df, user_query):
            Suggests the output type ('text', 'table', or 'plot') based on the DataFrame and user query.
        generate_chart(df, chart_type='bar', plot_backend=None):
            Generates a chart of the specified type using the provided or default plotting backend.
        available_chart_types():
            Returns the list of supported chart types.
        _default_plot_backend():
            Returns the default plotting backend (plotly.express).

    Example:
        engine = VisualizationEngine()
        output_type = engine.suggest_output_type(df, "Show me a trend of sales over time")
        if output_type == 'plot':
            fig = engine.generate_chart(df, chart_type='line')
            fig.show()
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        config: Optional[Any] = None,
        supported_types: Optional[List[str]] = None
    ):
        self.config = config or OpenAIConfig
        self.llm = llm_client or OpenAI(api_key=getattr(self.config, "OpenAI_API_KEY", None))
        self.supported_types = supported_types or ['line', 'bar', 'scatter', 'histogram', 'pie', 'trend']

    def suggest_output_type(self, df: pd.DataFrame, user_query: str) -> str:
        """
        Suggest output type ('text', 'table', or 'plot') based on dataframe and user query.
        Returns 'text' on error or if DataFrame is empty.
        """
        if df.empty:
            return 'text'

        column_info = ", ".join([f"{col} ({str(dtype)})" for col, dtype in df.dtypes.items()])
        prompt = (
            f"Data columns: {column_info}\n"
            f"User query: '{user_query}'\n"
            "Suggest output type: 'text', 'table', or 'plot'."
        )

        try:
            response = self.llm.chat.completions.create(
                model=getattr(self.config, "OpenAI_model", "gpt-4-turbo"),
                messages=[
                    {"role": "system", "content": "You are a visualization output expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.2,
                top_p=1.0
            )
            output_type = response.choices[0].message.content.strip().lower()
            return output_type if output_type in ['text', 'table', 'plot'] else 'text'
        except Exception as e:
            print(f"LLM output type suggestion error: {e}")
            return 'text'

    def generate_chart(
        self,
        df: pd.DataFrame,
        chart_type: str = 'bar',
        plot_backend: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Generate a chart using the specified backend (default: plotly.express).
        Returns the chart object or None if generation fails.
        """
        if chart_type not in self.supported_types:
            print(f"Unsupported chart type: {chart_type}. Supported types: {self.supported_types}")
            return None

        plot_backend = plot_backend or self._default_plot_backend()
        numeric = df.select_dtypes(include='number').columns.tolist()
        categoric = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime = df.select_dtypes(include='datetime').columns.tolist()

        try:
            # Enhanced: allow user to specify x/y columns, or pick best automatically
            def pick_first(lst):
                return lst[0] if lst else None

            if chart_type == 'line':
                x_col = pick_first(datetime) or pick_first(categoric)
                y_cols = numeric if len(numeric) > 1 else [pick_first(numeric)]
                if x_col and y_cols and any(y_cols):
                    return plot_backend.line(df.sort_values(x_col), x=x_col, y=y_cols)
                else:
                    print("Line plot requires at least one x (datetime/categorical) and one y (numeric) column.")
            elif chart_type == 'bar':
                x_col = pick_first(categoric) or pick_first(datetime)
                y_cols = numeric if len(numeric) > 1 else [pick_first(numeric)]
                if x_col and y_cols and any(y_cols):
                    return plot_backend.bar(df, x=x_col, y=y_cols)
                else:
                    print("Bar plot requires at least one x (categorical/datetime) and one y (numeric) column.")
            elif chart_type == 'scatter':
                if len(numeric) >= 2:
                    return plot_backend.scatter(df, x=numeric[0], y=numeric[1])
                else:
                    print("Scatter plot requires at least two numeric columns.")
            elif chart_type == 'histogram':
                if numeric:
                    return plot_backend.histogram(df, x=numeric[0])
                else:
                    print("Histogram plot requires at least one numeric column.")
            elif chart_type == 'pie':
                if categoric and numeric:
                    return plot_backend.pie(df, names=categoric[0], values=numeric[0])
                else:
                    print("Pie chart requires at least one categorical and one numeric column.")
        except Exception as e:
            print(f"Plot generation error: {e}")

        print("Could not generate chart with the provided data and chart type.")
        return None

    def available_chart_types(self) -> List[str]:
        """
        Returns the list of supported chart types.
        """
        return self.supported_types

    @staticmethod
    def _default_plot_backend():
        import plotly.express as px
        return px