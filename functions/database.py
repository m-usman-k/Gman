import sqlite3


from config import DATABASE_PATH

def db_connection():
    connection = sqlite3.connect(database=DATABASE_PATH)
    return connection

def setup_tables():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY NOT NULL,
                points INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        cursor.close()