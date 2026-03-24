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
            first_seen_at TEXT NOT NULL
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


def get_item_id_by_url(conn: sqlite3.Connection, url: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM items WHERE url = ?",
        (url,),
    ).fetchone()

    if row is None:
        return None

    return int(row["id"])


def insert_item(
    conn: sqlite3.Connection,
    *,
    title: str,
    url: str,
    raw_text: str,
    source_type: str,
    first_seen_at: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO items (url, title, raw_text, source_type, first_seen_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (url, title, raw_text, source_type, first_seen_at),
    )
    conn.commit()
    return int(cursor.lastrowid)


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


def get_all_items_with_members(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT
            items.id,
            items.title,
            items.url,
            items.source_type,
            items.first_seen_at,
            item_members.member_name
        FROM items
        JOIN item_members
          ON items.id = item_members.item_id
        ORDER BY items.first_seen_at DESC, items.id DESC
        """
    ).fetchall()

    return list(rows)