import unittest

class MyTestCase(unittest.TestCase):
    def test_sql_query_generation(self):
        # Arrange
        expected_query = "SELECT * FROM users WHERE age > 30"
        
        # Act - call the function
        generated_query = generate_sql_query("users", "age > 30")
        
        # Assert
        self.assertEqual(generated_query, expected_query)
    def test_sql_query_generation_with_limit(self):
        # Arrange
        expected_query = "SELECT * FROM users WHERE age > 30 LIMIT 10"
        
        # Act - call the function
        generated_query = generate_sql_query("users", "age > 30", limit=10)
        
        # Assert
        self.assertEqual(generated_query, expected_query)
    def test_sql_query_generation_with_order_by(self):
        # Arrange
        expected_query = "SELECT * FROM users WHERE age > 30 ORDER BY name ASC"
        
        # Act - call the function
        generated_query = generate_sql_query("users", "age > 30", order_by="name ASC")
        
        # Assert
        self.assertEqual(generated_query, expected_query)
    def test_sql_query_generation_with_limit_and_order_by(self):
        # Arrange
        expected_query = "SELECT * FROM users WHERE age > 30 ORDER BY name ASC LIMIT 10"
        
        # Act - call the function
        generated_query = generate_sql_query("users", "age > 30", order_by="name ASC", limit=10)
        
        # Assert
        self.assertEqual(generated_query, expected_query)
def generate_sql_query(table, condition, order_by=None, limit=None):
    query = f"SELECT * FROM {table} WHERE {condition}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit:
        query += f" LIMIT {limit}"
    return query
    

if __name__ == '__main__':
    unittest.main()