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

def migrate_bosses():

    conn = get_connection()
    cursor = conn.cursor()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    bosses_file = os.path.join(base_dir, "bosses.json")

    if not os.path.exists(bosses_file):
        print("bosses.json не найден")
        conn.close()
        return

    import json

    with open(
        bosses_file,
        "r",
        encoding="utf-8"
    ) as f:
        bosses = json.load(f)

    for boss in bosses:

        cursor.execute(
            """
            INSERT INTO bosses (
                id,
                name,
                location,
                type,
                defeated
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                location = EXCLUDED.location,
                type = EXCLUDED.type
            """,
            (
                boss["id"],
                boss["name"],
                boss.get("location", ""),
                boss.get("type", ""),
                boss.get("defeated", False)
            )
        )

    conn.commit()

    cursor.close()
    conn.close()

    print(f"Мигрировано боссов: {len(bosses)}")

if __name__ == "__main__":

    init_db()
    migrate_bosses()

    print("PostgreSQL database initialized")
