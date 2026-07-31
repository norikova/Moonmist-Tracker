import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL")
DB = "moonmist.db"


def get_connection():

    # Render / PostgreSQL
    if DATABASE_URL:

        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor

        return conn

    # Локально / SQLite
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:

        # PostgreSQL
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

    else:

        # SQLite
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS kills (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            boss_id INTEGER,

            boss_name TEXT,

            location TEXT,

            attempts INTEGER,

            date TEXT

        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            boss_id INTEGER,

            boss_name TEXT,

            location TEXT,

            date TEXT

        )
        """)

    conn.commit()
    conn.close()


if __name__ == "__main__":

    init_db()

    print("Database created")
