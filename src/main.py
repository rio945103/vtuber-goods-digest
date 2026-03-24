from datetime import datetime
import requests

from settings import load_env_settings, load_members
from fetchers.nijisanji_store import create_session, fetch_html
from parsers.nijisanji_parser import parse_member_items
from filters.item_filter import build_item_label, build_sort_key, should_include_item
from db import (
    connect_db,
    get_item_id_by_url,
    init_db,
    insert_item,
    link_item_member,
)
from notifiers.discord_notifier import build_discord_message, send_discord_message


def main() -> None:
    env_settings = load_env_settings()
    db_path = env_settings["DATABASE_PATH"]
    webhook_url = env_settings["DISCORD_WEBHOOK_URL"]

    conn = connect_db(db_path)
    init_db(conn)

    members = load_members()
    session = create_session()

    new_items_summary: list[tuple[str, tuple[int, int, int], str, str, str]] = []
    current_run_new_urls: set[str] = set()
    failed_members: list[tuple[str, str]] = []

    for member in members:
        member_name = member["display_name"]
        store_url = member["store_url"]

        print("=" * 60)
        print(f"対象: {member_name}")
        print(f"URL: {store_url}")

        try:
            html = fetch_html(session, store_url)
        except requests.RequestException as e:
            print(f"取得失敗: {member_name}")
            print(f"理由: {e}")
            failed_members.append((member_name, str(e)))
            continue

        items = parse_member_items(
            html=html,
            base_url=store_url,
            member_name=member_name,
        )

        filtered_items = [item for item in items if should_include_item(item)]

        print(f"抽出件数: {len(items)}")
        print(f"フィルタ後件数: {len(filtered_items)}")

        for order_index, item in enumerate(filtered_items):
            label = build_item_label(item)
            sort_key = build_sort_key(item, order_index)
            existing_item_id = get_item_id_by_url(conn, item.url)

            if existing_item_id is None:
                item_id = insert_item(
                    conn,
                    title=item.title,
                    url=item.url,
                    raw_text=item.raw_text,
                    source_type=item.source_type,
                    first_seen_at=datetime.now().isoformat(timespec="seconds"),
                )
                link_item_member(conn, item_id=item_id, member_name=item.member_name)

                current_run_new_urls.add(item.url)
                new_items_summary.append((item.member_name, sort_key, label, item.title, item.url))
            else:
                link_item_member(
                    conn,
                    item_id=existing_item_id,
                    member_name=item.member_name,
                )

                if item.url in current_run_new_urls:
                    new_items_summary.append((item.member_name, sort_key, label, item.title, item.url))

    print("\n" + "=" * 60)
    print("今回新しく保存された商品")
    print("=" * 60)

    if not new_items_summary:
        print("新着はありませんでした。")
    else:
        sorted_summary = sorted(new_items_summary, key=lambda x: (x[0], x[1]))

        for member_name, _, label, title, url in sorted_summary:
            print(f"[{member_name}] {label} {title}")
            print(url)
            print("-" * 40)

        message = build_discord_message(sorted_summary)

        print("\n" + "=" * 60)
        print("Discord送信内容")
        print("=" * 60)
        print(message)

        try:
            send_discord_message(webhook_url, message)
            if webhook_url.strip():
                print("\nDiscordに送信しました。")
            else:
                print("\nWebhook URL が空なので、Discord送信はスキップしました。")
        except requests.RequestException as e:
            print(f"\nDiscord送信失敗: {e}")

    if failed_members:
        print("\n" + "=" * 60)
        print("取得失敗メンバー")
        print("=" * 60)
        for member_name, reason in failed_members:
            print(f"{member_name}: {reason}")


if __name__ == "__main__":
    main()