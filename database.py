import os
import psycopg2
from psycopg2.extras import RealDictCursor


DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL не задана в переменных окружения"
        )

    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )

    return conn


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kills (

        id SERIAL PRIMARY KEY,

        boss_id INTEGER,

        boss_name TEXT,

        location TEXT,

        attempts INTEGER,

        date TEXT

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attempts (

        id SERIAL PRIMARY KEY,

        boss_id INTEGER,

        boss_name TEXT,

        location TEXT,

        date TEXT

    )
    """)

    conn.commit()

    cursor.close()
    conn.close()


if __name__ == "__main__":

    init_db()

    print("PostgreSQL database initialized")
