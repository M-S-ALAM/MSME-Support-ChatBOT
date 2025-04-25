import sqlite3

def print_table_info(cursor):
    """Print the columns and data types for each table in the database."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Database Tables and their schema:")
    for table in tables:
        print(f"\nTable: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for column in columns:
            print(f"Column: {column[1]}, Type: {column[2]}")

def print_table_data(cursor):
    """Print all data from all tables in the database."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        print(f"\nData from Table: {table[0]}")
        cursor.execute(f"SELECT * FROM {table[0]}")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

def main():
    # Connect to the SQLite database
    conn = sqlite3.connect('Database/sqlite-sakila.db')
    cursor = conn.cursor()

    # Print table information (columns and types)
    print_table_info(cursor)

    # Print all data from all tables
    #print_table_data(cursor)

    # Close the connection
    conn.close()

if __name__ == "__main__":
    main()
