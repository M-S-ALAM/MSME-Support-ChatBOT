import pandas as pd
import plotly.express as px
import streamlit as st
from openai import OpenAI
from modular_code.config import ChatGPTConfig
from typing import List

class VisualizationEngine:
    def __init__(self, llm=None):
        self.supported_types = ['line', 'bar', 'scatter', 'histogram', 'pie', 'trend']
        self.llm = llm
        self.client = OpenAI(api_key=ChatGPTConfig.API_KEY) if llm is None else None

    def suggest_visualization_types(self, df: pd.DataFrame, user_query: str) -> List[str]:
        if df.empty:
            return ['table']

        column_info = ", ".join([f"{col} ({str(dtype)})" for col, dtype in df.dtypes.items()])
        prompt = (
            "You are a data visualization expert.\n\n"
            f"DataFrame Columns and Types:\n{column_info}\n\n"
            f"User Query:\n'{user_query}'\n\n"
            f"From this list: {self.supported_types}, which visualization types are best suited for this data and query?\n"
            "Respond with a comma-separated list like: 'bar, pie, scatter'.\n"
            "If none are relevant, respond with: 'None'."
        )

        try:
            if self.client:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are a data visualization expert."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.3,
                    top_p=1.0
                )
                raw_output = response.choices[0].message.content.strip().lower()
            else:
                raw_output = self.llm.predict(prompt).strip().lower()

            vis_types = [v.strip() for v in raw_output.split(',') if v.strip() in self.supported_types]
            return vis_types if vis_types else None

        except Exception as e:
            st.warning(f"⚠️ LLM error: {e}")
            return ['table']

    def generate_chart(self, df: pd.DataFrame, chart_type: str):
        if df.empty:
            st.warning("⚠️ No data available for visualization.")
            return None

        numeric = df.select_dtypes(include='number').columns.tolist()
        categoric = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime = df.select_dtypes(include='datetime').columns.tolist()
        df = df.dropna().copy()

        try:
            if chart_type in ["line", "trend"] and datetime and numeric:
                return px.line(df.sort_values(datetime[0]), x=datetime[0], y=numeric[0],
                               title=f"📈 Trend Over Time ({numeric[0]})")
            elif chart_type == "bar":
                if len(categoric) >= 2 and numeric:
                    combo = df[categoric].astype(str).agg('-'.join, axis=1)
                    return px.bar(df, x=combo, y=numeric[0], title="📊 Grouped Bar Chart")
                elif categoric and numeric:
                    return px.bar(df, x=categoric[0], y=numeric[0], title="📊 Category Bar Chart")
            elif chart_type == "scatter" and len(numeric) >= 2:
                return px.scatter(df, x=numeric[0], y=numeric[1], title="🔎 Scatter Plot")
            elif chart_type == "histogram" and numeric:
                return px.histogram(df, x=numeric[0], title="📉 Distribution")
            elif chart_type == "pie" and categoric and numeric:
                return px.pie(df, names=categoric[0], values=numeric[0], title="🥧 Pie Chart")

        except Exception as e:
            st.warning(f"⚠️ Chart rendering failed: {e}")

        return None

