import unittest

from src.mcp.sql_query_generation import SQLQueryGenerator


class TestSQLQueryGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = SQLQueryGenerator(llm_client=None)  # Use None to skip LLM for logic tests

    def test_clean_sql_query_valid(self):
        sql = "SELECT * FROM sales;"
        self.assertEqual(self.generator.clean_sql_query(sql), sql)

    def test_clean_sql_query_with_code_block(self):
        sql = "```sql\nSELECT * FROM sales;\n```"
        self.assertEqual(self.generator.clean_sql_query(sql), "SELECT * FROM sales;")

    def test_clean_sql_query_no_sql(self):
        sql = "NO_SQL"
        self.assertIsNone(self.generator.clean_sql_query(sql))

    def test_clean_sql_query_invalid(self):
        sql = "This is not a SQL query"
        self.assertIsNone(self.generator.clean_sql_query(sql))

    def test_clean_sql_query_lowercase_no_sql(self):
        sql = "no_sql"
        self.assertIsNone(self.generator.clean_sql_query(sql))

if __name__ == '__main__':
    unittest.main()
