import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB = os.path.join(BASE_DIR, "moonmist.db")


def get_connection():

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    return conn



def init_db():

    conn = get_connection()

    cursor = conn.cursor()


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
