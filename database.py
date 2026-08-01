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

    # Убийства
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

    # Смерти / попытки
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attempts (

        id SERIAL PRIMARY KEY,

        boss_id INTEGER,

        boss_name TEXT,

        location TEXT,

        date TEXT

    )
    """)

    # Боссы
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bosses (

        id INTEGER PRIMARY KEY,

        name TEXT NOT NULL,

        location TEXT,

        type TEXT,

        defeated BOOLEAN DEFAULT FALSE

    )
    """)

    # Текущий бой
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS current (

        id INTEGER PRIMARY KEY,

        boss_id INTEGER,

        boss_name TEXT,

        location TEXT,

        deaths INTEGER DEFAULT 0

    )
    """)

    # Гарантируем одну запись текущего состояния
    cursor.execute("""
    INSERT INTO current (
        id,
        boss_id,
        boss_name,
        location,
        deaths
    )
    VALUES (
        1,
        NULL,
        'Не выбран',
        '',
        0
    )
    ON CONFLICT (id) DO NOTHING
    """)

    conn.commit()

    cursor.close()
    conn.close()


if __name__ == "__main__":

    init_db()

    print("PostgreSQL database initialized")
