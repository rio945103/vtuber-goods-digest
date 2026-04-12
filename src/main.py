#日付時刻のためのモジュール
from datetime import datetime
# HTTPリクエストを送るためのライブラリ
import requests

from settings import load_env_settings, load_members
from fetchers.nijisanji_store import create_session, fetch_html
from parsers.nijisanji_parser import parse_member_items
from filters.item_filter import (
    build_item_label,
    build_sort_key,
    detect_sale_status,
    should_include_item,
)
from db import (
    connect_db,
    get_item_by_url,
    init_db,
    insert_item,
    link_item_member,
    mark_notification_sent,
    update_item_snapshot,
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
    current_run_notified: dict[str, str] = {}
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
            sale_status = detect_sale_status(item)
            now_str = datetime.now().isoformat(timespec="seconds")

            existing_item = get_item_by_url(conn, item.url)

            if existing_item is None:
                item_id = insert_item(
                    conn,
                    title=item.title,
                    url=item.url,
                    raw_text=item.raw_text,
                    source_type=item.source_type,
                    current_status=sale_status,
                    first_seen_at=now_str,
                    last_seen_at=now_str,
                )
                link_item_member(conn, item_id=item_id, member_name=item.member_name)

                if sale_status in ("upcoming", "on_sale"):
                    mark_notification_sent(conn, item_id=item_id, sale_status=sale_status)
                    current_run_notified[item.url] = sale_status
                    new_items_summary.append(
                        (item.member_name, sort_key, label, item.title, item.url)
                    )
                continue

            item_id = int(existing_item["id"])
            link_item_member(conn, item_id=item_id, member_name=item.member_name)

            update_item_snapshot(
                conn,
                item_id=item_id,
                title=item.title,
                raw_text=item.raw_text,
                source_type=item.source_type,
                current_status=sale_status,
                last_seen_at=now_str,
            )

            # 同じ実行中に別メンバーでも同じ商品が通知対象になった時は、そのメンバーにも表示する
            if current_run_notified.get(item.url) == sale_status:
                new_items_summary.append(
                    (item.member_name, sort_key, label, item.title, item.url)
                )
                continue

            upcoming_notified = int(existing_item["upcoming_notified"])
            on_sale_notified = int(existing_item["on_sale_notified"])

            should_notify = False

            if sale_status == "upcoming" and upcoming_notified == 0:
                should_notify = True

            if sale_status == "on_sale" and on_sale_notified == 0:
                should_notify = True

            if should_notify:
                mark_notification_sent(conn, item_id=item_id, sale_status=sale_status)
                current_run_notified[item.url] = sale_status
                new_items_summary.append(
                    (item.member_name, sort_key, label, item.title, item.url)
                )

    print("\n" + "=" * 60)
    print("今回通知対象になった商品")
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