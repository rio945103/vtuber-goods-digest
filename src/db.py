import sqlite3
from pathlib import Path


def connect_db(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            source_type TEXT NOT NULL,
            current_status TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            upcoming_notified INTEGER NOT NULL DEFAULT 0,
            on_sale_notified INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS item_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            member_name TEXT NOT NULL,
            UNIQUE(item_id, member_name),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
        """
    )

    conn.commit()


def get_item_by_url(conn: sqlite3.Connection, url: str) -> sqlite3.Row | None:
    row = conn.execute(
        "SELECT * FROM items WHERE url = ?",
        (url,),
    ).fetchone()

    return row


def insert_item(
    conn: sqlite3.Connection,
    *,
    title: str,
    url: str,
    raw_text: str,
    source_type: str,
    current_status: str,
    first_seen_at: str,
    last_seen_at: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO items (
            url, title, raw_text, source_type,
            current_status, first_seen_at, last_seen_at,
            upcoming_notified, on_sale_notified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
        """,
        (
            url,
            title,
            raw_text,
            source_type,
            current_status,
            first_seen_at,
            last_seen_at,
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def update_item_snapshot(
    conn: sqlite3.Connection,
    *,
    item_id: int,
    title: str,
    raw_text: str,
    source_type: str,
    current_status: str,
    last_seen_at: str,
) -> None:
    conn.execute(
        """
        UPDATE items
        SET
            title = ?,
            raw_text = ?,
            source_type = ?,
            current_status = ?,
            last_seen_at = ?
        WHERE id = ?
        """,
        (
            title,
            raw_text,
            source_type,
            current_status,
            last_seen_at,
            item_id,
        ),
    )
    conn.commit()


def mark_notification_sent(
    conn: sqlite3.Connection,
    *,
    item_id: int,
    sale_status: str,
) -> None:
    if sale_status == "upcoming":
        conn.execute(
            """
            UPDATE items
            SET upcoming_notified = 1
            WHERE id = ?
            """,
            (item_id,),
        )
    elif sale_status == "on_sale":
        conn.execute(
            """
            UPDATE items
            SET on_sale_notified = 1
            WHERE id = ?
            """,
            (item_id,),
        )

    conn.commit()


def link_item_member(
    conn: sqlite3.Connection,
    *,
    item_id: int,
    member_name: str,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO item_members (item_id, member_name)
        VALUES (?, ?)
        """,
        (item_id, member_name),
    )
    conn.commit()