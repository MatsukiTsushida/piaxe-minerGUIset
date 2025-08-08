import psycopg2
from psycopg2 import sql, Error
import pandas as pd
from contextlib import contextmanager

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',  # Change if your PostgreSQL is on a different host
    'database': 'postgres',
    'user': 'postgres',  # Change if you have a different username
    'password': '1324',
    'port': 5432
}

class PostgreSQLConnection:
    def __init__(self, config=None):
        self.config = config or DB_CONFIG
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.config)
            self.cursor = self.connection.cursor()
            print("Successfully connected to PostgreSQL database")
            return True
        except Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            print('CLOSED1')
            self.cursor.close()
        if self.connection:
            print('CLOSED2')
            self.connection.close()
        print("PostgreSQL connection closed")

    def execute_query(self, query, params=None, fetch=True):
        """Execute a query and return results"""
        try:
            self.cursor.execute(query, params)
            if fetch:
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
        except Error as e:
            print(f"Error executing query: {e}")
            self.connection.rollback()
            return None

    def fetch_to_dataframe(self, query, params=None):
        """Execute query and return results as pandas DataFrame"""
        try:
            return pd.read_sql_query(query, self.connection, params=params)
        except Error as e:
            print(f"Error fetching data to DataFrame: {e}")
            return None

# Context manager for automatic connection handling
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    db = PostgreSQLConnection()
    try:
        if db.connect():
            yield db
        else:
            yield None
    finally:
        db.disconnect()

# Simple connection function
def create_connection():
    """Simple function to create a database connection"""
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        print("Database connection successful")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# Example usage functions
def example_basic_usage():
    """Example of basic database operations"""
    db = PostgreSQLConnection()

    if db.connect():
        # Example query
        result = db.execute_query("SELECT version();")
        if result:
            print(f"PostgreSQL version: {result[0][0]}")

        # Example with DataFrame (useful for Grafana data)
        df = db.fetch_to_dataframe("SELECT NOW() as current_time;")
        if df is not None:
            print(df)

        db.disconnect()

def example_context_manager():
    """Example using context manager"""
    with get_db_connection() as db:
        if db:
            # Your database operations here
            result = db.execute_query("SELECT current_database();")
            if result:
                print(f"Current database: {result[0][0]}")

def example_for_grafana_data():
    """Example function that could be used to prepare data for Grafana"""
    with get_db_connection() as db:
        if db:
            # Example time-series query (common for Grafana)
            query = """
            SELECT
                NOW() - INTERVAL '1 hour' * generate_series(0, 23) as time,
                random() * 100 as value
            ORDER BY time;
            """

            df = db.fetch_to_dataframe(query)
            if df is not None:
                print("Sample time-series data for Grafana:")
                print(df.head())
                return df
    return None

if __name__ == "__main__":
    print("Testing PostgreSQL connection...")

    # Test basic connection
    example_basic_usage()

    print("\n" + "="*50 + "\n")

    # Test context manager
    example_context_manager()

    print("\n" + "="*50 + "\n")

    # Test Grafana-style data query
    example_for_grafana_data()
