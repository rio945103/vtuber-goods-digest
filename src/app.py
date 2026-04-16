from flask import Flask, render_template
from pathlib import Path
from db import connect_db
from settings import load_env_settings

app = Flask(__name__)

env_settings = load_env_settings()

BASE_DIR = Path(__file__).resolve().parent.parent
db_path_raw = env_settings["DATABASE_PATH"]
db_path = str(BASE_DIR / db_path_raw) if not Path(db_path_raw).is_absolute() else db_path_raw


@app.route("/")
def index():
    conn = connect_db(db_path)
    cursor = conn.execute("""
        SELECT
            i.id,
            i.title,
            i.url,
            i.current_status,
            i.first_seen_at,
            GROUP_CONCAT(im.member_name, ', ') AS members
        FROM items i
        LEFT JOIN item_members im ON i.id = im.item_id
        GROUP BY i.id
        ORDER BY i.first_seen_at DESC
    """)
    items = cursor.fetchall()
    conn.close()
    return render_template("index.html", items=items)


if __name__ == "__main__":
    app.run(debug=True)