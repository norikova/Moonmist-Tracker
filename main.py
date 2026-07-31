from flask import Flask, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import json
import os
from database import get_connection, init_db

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.json.ensure_ascii = False
CORS(app)

BOSSES_FILE = os.path.join(BASE_DIR, "bosses.json")

CURRENT_FILE = os.path.join(BASE_DIR, "current.json")

ATTEMPTS_FILE = os.path.join(BASE_DIR, "attempts.json")

HISTORY_FILE = os.path.join(BASE_DIR, "history.json")


def load_current():

    if os.path.exists(CURRENT_FILE):

        with open(
            CURRENT_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)


    return {
        "boss_id": None,
        "boss_name": "Не выбран",
        "deaths": 0
    }



def save_current(data):

    with open(
        CURRENT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

def load_attempts():

    if os.path.exists(ATTEMPTS_FILE):

        with open(
            ATTEMPTS_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    return []



def save_attempts(data):

    with open(
        ATTEMPTS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

def load_bosses():
    if os.path.exists(BOSSES_FILE):
        with open(BOSSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return []

def load_history():

    if os.path.exists(HISTORY_FILE):

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    return []



def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )

def save_bosses(bosses):
    with open(BOSSES_FILE, "w", encoding="utf-8") as f:
        json.dump(
            bosses,
            f,
            ensure_ascii=False,
            indent=2
        )


@app.route("/")
def home():
    return "EldenTracker is running!"


# Получить всех боссов
@app.route("/bosses")
def bosses():
    return jsonify(load_bosses())


# Статистика
@app.route("/data")
def data():

    current = load_current()

    bosses = load_bosses()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM kills
        """
    )
    
    killed = cursor.fetchone()["count"]

    conn.close()

    total = len(bosses)

    return jsonify({

        "bosses_killed": killed,

        "total_bosses": total,

        "progress":
        round(killed / total * 100,1)
        if total else 0,

        "current_boss":
        current.get(
            "boss_name",
            "Не выбран"
        ),

        "current_location":
        current.get(
            "location",
            ""
        ),

        "deaths":
        current.get(
            "deaths",
            0
        )

    })

@app.route("/select/<int:boss_id>", methods=["POST"])
def select_boss(boss_id):

    bosses = load_bosses()

    for boss in bosses:

        if boss["id"] == boss_id and not boss.get("defeated", False):

            current = {

                "boss_id": boss_id,

                "boss_name": boss["name"],

                 "location": boss["location"],

                 "deaths": 0

            }


            save_current(current)


            return jsonify({
                "success":True
            })


    return jsonify({
        "success":False
    })

@app.route("/death", methods=["POST"])
def death():

    current = load_current()


    if current["boss_id"] is None:

        return jsonify({
            "success": False,
            "error": "No boss selected"
        })


    # увеличиваем счетчик текущего боя

    current["deaths"] += 1

    save_current(current)



    # сохраняем попытку в базу данных

    from datetime import datetime


    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO attempts
        (
            boss_id,
            boss_name,
            location,
            date
        )

        VALUES (%s, %s, %s, %s)
        """,

        (
            current["boss_id"],
            current["boss_name"],
            current.get("location",""),
            datetime.now().strftime("%d.%m.%Y %H:%M")
        )

    )


    conn.commit()
    conn.close()



    return jsonify(current)

@app.route("/undo_death", methods=["POST"])
def undo_death():

    current = load_current()

    if current["boss_id"] is None:
        return jsonify({
            "success": False,
            "error": "No boss selected"
        })

    if current["deaths"] <= 0:
        return jsonify({
            "success": False,
            "error": "Нет смертей для отката"
        })

    conn = get_connection()
    cursor = conn.cursor()

    # Удаляем последнюю запись о смерти
    cursor.execute(
        """
        DELETE FROM attempts
        WHERE id = (
            SELECT id
            FROM attempts
            WHERE boss_id = %s
            ORDER BY id DESC
            LIMIT 1
        )
        """,
        (current["boss_id"],)
    )

    # Проверяем, действительно ли запись была удалена
    if cursor.rowcount == 0:
        conn.close()

        return jsonify({
            "success": False,
            "error": "Запись смерти не найдена в базе"
        })

    conn.commit()
    conn.close()

    # Уменьшаем текущий счётчик
    current["deaths"] -= 1

    save_current(current)

    return jsonify(current)

@app.route("/kill_current", methods=["POST"])
def kill_current():

    current = load_current()

    boss_id = current["boss_id"]


    if boss_id is None:

        return jsonify({
            "success": False,
            "error": "No boss selected"
        })


    bosses = load_bosses()


    boss_name = current["boss_name"]


    from datetime import datetime


    # запись победы в SQLite

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO kills
        (
            boss_id,
            boss_name,
            location,
            attempts,
            date
        )

        VALUES (%s, %s, %s, %s, %s)
        """,

        (
            boss_id,
            boss_name,
            current.get("location", ""),
            current["deaths"],
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )


    conn.commit()
    conn.close()



    # отмечаем босса убитым

    for boss in bosses:

        if boss["id"] == boss_id:

            boss["defeated"] = True



    save_bosses(bosses)



    # очищаем текущий бой

    save_current({

        "boss_id": None,

        "boss_name": "Не выбран",

        "location": "",

        "deaths": 0

    })



    
    return jsonify({

        "success": True

    })
# ОТМЕНА ПОСЛЕДНЕГО УБИЙСТВА
@app.route("/undo_kill", methods=["POST"])
def undo_kill():

    current = load_current()

    # После убийства current очищается,
    # поэтому F8 можно использовать только когда
    # сейчас нет активного босса.
    if current["boss_id"] is not None:
        return jsonify({
            "success": False,
            "error": "Сначала должен быть завершён текущий бой"
        })

    conn = get_connection()
    cursor = conn.cursor()

    # Берём последнее убийство
    cursor.execute(
        """
        SELECT
            id,
            boss_id,
            boss_name,
            location,
            attempts
        FROM kills
        ORDER BY id DESC
        LIMIT 1
        """
    )

    kill = cursor.fetchone()

    if kill is None:
        conn.close()

        return jsonify({
            "success": False,
            "error": "Записей об убийствах нет"
        })

    # Удаляем последнее убийство
    cursor.execute(
        """
        DELETE FROM kills
        WHERE id = %s
        """,
        (kill["id"],)
    )

    conn.commit()
    conn.close()

    # Возвращаем босса в bosses.json
    bosses = load_bosses()

    for boss in bosses:

        if boss["id"] == kill["boss_id"]:

            boss["defeated"] = False

            break

    save_bosses(bosses)

    # Восстанавливаем текущий бой
    save_current({

        "boss_id": kill["boss_id"],

        "boss_name": kill["boss_name"],

        "location": kill["location"],

        "deaths": kill["attempts"]

    })

    return jsonify({
        "success": True,

        "boss_id": kill["boss_id"],

        "boss_name": kill["boss_name"],

        "location": kill["location"],

        "deaths": kill["attempts"]

    })


# Вернуть босса обратно
@app.route("/boss/<int:boss_id>/reset", methods=["POST"])
def reset_boss(boss_id):
    bosses = load_bosses()

    for boss in bosses:
        if boss["id"] == boss_id:
            boss["defeated"] = False
            save_bosses(bosses)

            return jsonify({
                "success": True
            })

    return jsonify({
        "success": False
    }), 404

@app.route("/history-data")
def history_data():

    return jsonify(load_history())

@app.route("/stats")
def stats():

    bosses = load_bosses()


    conn = get_connection()

    cursor = conn.cursor()



    # количество убитых боссов

    cursor.execute(
        """
        SELECT COUNT(*) 
        FROM kills
        """
    )
    
    killed = cursor.fetchone()["count"]



    total = len(bosses)



    # все попытки

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM attempts
        """
    )
    
    total_deaths = cursor.fetchone()["count"]



    # топ сложных боссов

    cursor.execute(
        """
        SELECT 
            boss_name,
            COUNT(*) as deaths
    
        FROM attempts
    
        GROUP BY boss_name
    
        ORDER BY deaths DESC
    
        LIMIT 3
        """
    )
    
    top_deadly = cursor.fetchall()



    # последние победы

    cursor.execute(
        """
        SELECT
            boss_id,
            boss_name,
            location,
            attempts,
            date
    
        FROM kills
    
        ORDER BY id DESC
    
        LIMIT 10
        """
    )
    
    history = cursor.fetchall()



    conn.close()



    return jsonify({

        "total_bosses": total,

        "killed": killed,

        "left": total - killed,


        "total_deaths": total_deaths,


        "top_deadly": [

            {
                "name": row["boss_name"],
                "deaths": row["deaths"]
            }

            for row in top_deadly

        ],


        "history": [

            dict(row)

            for row in history

        ]

    })

@app.route("/tracker")
def tracker():
    print("ОТДАЮ TRACKER:", os.path.abspath("tracker.html"))
    return send_file("tracker.html")


@app.route("/boss_stats")
def boss_stats():

    bosses = load_bosses()


    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute(
        """
        SELECT
            boss_id,
            COUNT(*) as deaths
    
        FROM attempts
    
        GROUP BY boss_id
        """
    )
    
    attempts = cursor.fetchall()



    cursor.execute(
        """
        SELECT
            boss_id,
            date
    
        FROM kills
        """
    )
    
    kills = cursor.fetchall()



    conn.close()



    death_map = {

        row["boss_id"]: row["deaths"]

        for row in attempts

    }



    kill_map = {

        row["boss_id"]: row["date"]

        for row in kills

    }



    locations = {}



    for boss in bosses:


        boss_data = {

            "id": boss["id"],

            "name": boss["name"],

            "type": boss.get("type",""),


            "deaths":
            death_map.get(
                boss["id"],
                0
            ),


            "defeated":
            boss.get(
                "defeated",
                False
            ),


            "killed_date":
            kill_map.get(
                boss["id"]
            )

        }



        location = boss["location"]



        if location not in locations:

            locations[location] = []



        locations[location].append(
            boss_data
        )



    return jsonify(locations)

@app.route("/overlay")
def overlay():
    return send_file(
    os.path.join(BASE_DIR, "overlay.html")
)

@app.route("/history")
def history():
    return send_file(
        os.path.join(BASE_DIR, "history.html")
    )


init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

# python main.py
