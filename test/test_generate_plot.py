import unittest
import pandas as pd

from src.mcp.generate_plot import VisualizationEngine

class TestVisualizationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = VisualizationEngine(llm_client=None)  # Use None to skip LLM for chart tests

    def test_generate_bar_chart(self):
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 30]
        })
        chart = self.engine.generate_chart(df, chart_type='bar')
        self.assertIsNotNone(chart)

    def test_generate_line_chart(self):
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=3),
            'value': [1, 2, 3]
        })
        chart = self.engine.generate_chart(df, chart_type='line')
        self.assertIsNotNone(chart)

    def test_generate_scatter_chart(self):
        df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        chart = self.engine.generate_chart(df, chart_type='scatter')
        self.assertIsNotNone(chart)

    def test_generate_histogram(self):
        df = pd.DataFrame({
            'value': [1, 2, 2, 3, 3, 3]
        })
        chart = self.engine.generate_chart(df, chart_type='histogram')
        self.assertIsNotNone(chart)

    def test_generate_pie_chart(self):
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 30]
        })
        chart = self.engine.generate_chart(df, chart_type='pie')
        self.assertIsNotNone(chart)

    def test_unsupported_chart_type(self):
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        chart = self.engine.generate_chart(df, chart_type='unknown')
        self.assertIsNone(chart)

    def test_generate_large_bar_chart(self):
        df = pd.DataFrame({
            'category': [f'Cat{i}' for i in range(100)],
            'value': [i * 10 for i in range(100)]
        })
        chart = self.engine.generate_chart(df, chart_type='bar')
        self.assertIsNotNone(chart)

    def test_generate_large_line_chart(self):
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=200),
            'value': [i for i in range(200)]
        })
        chart = self.engine.generate_chart(df, chart_type='line')
        self.assertIsNotNone(chart)

if __name__ == '__main__':
    unittest.main()