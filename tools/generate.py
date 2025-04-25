import pandas as pd
import numpy as np
from sqlalchemy import create_engine


class DataGenerator:
    def __init__(self, db_user, db_password, db_host, db_name):
        self.table_name = "web_form_list_column_id_seq"
        self.column_names = [
            "next_not_cached_value", "minimum_value", "maximum_value", "start_value",
            "increment", "cache_size", "cycle_option", "cycle_count"
        ]
        self.data_types = [
            "bigint(21)", "bigint(21)", "bigint(21)", "bigint(21)", "bigint(21)",
            "bigint(21) unsigned", "tinyint(1) unsigned", "bigint(21)"
        ]
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_name = db_name
        self.engine = self.create_db_connection()

    def create_db_connection(self):
        return create_engine(f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}/{self.db_name}")

    def generate_data(self, num_rows=10):
        data = {
            "next_not_cached_value": np.random.randint(100, 1000, num_rows),
            "minimum_value": np.random.randint(50, 500, num_rows),
            "maximum_value": np.random.randint(1000, 2000, num_rows),
            "start_value": np.random.randint(0, 100, num_rows),
            "increment": np.random.randint(1, 10, num_rows),
            "cache_size": np.random.randint(100, 500, num_rows),
            "cycle_option": np.random.choice([0, 1], num_rows),
            "cycle_count": np.random.randint(1, 10, num_rows)
        }
        return pd.DataFrame(data, columns=self.column_names)

    def insert_data_into_db(self, df):
        df.to_sql(name=self.table_name, con=self.engine, if_exists="replace", index=False)

    def run(self, num_rows=10):
        df = self.generate_data(num_rows)
        self.insert_data_into_db(df)
        return df


# Example usage
db_user = "shobot"
db_password = "shobot"
db_host = "localhost"
db_name = "walmart_chatbot_dummy"

data_generator = DataGenerator(db_user, db_password, db_host, db_name)
df = data_generator.run()
print(df)
