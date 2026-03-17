import mysql.connector
import os


def get_connection():
    """Create and return a MySQL database connection using environment variables."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "taskuser"),
        password=os.getenv("DB_PASSWORD", "taskpass"),
        database=os.getenv("DB_NAME", "taskdb"),
        autocommit=False,
    )
