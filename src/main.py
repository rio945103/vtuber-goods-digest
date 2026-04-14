#日付時刻のためのモジュール
from datetime import datetime
# HTTPリクエストを送るためのライブラリ
import requests
#settingsファイルからload_env_settingsとload_members関数をインポート
from settings import load_env_settings, load_members
#fetchersのnijisanji_storeからcreate_sessionとfetch_html関数をインポート
from fetchers.nijisanji_store import create_session, fetch_html
#parsersのnijisanji_parserからparse_member_items関数をインポート
from parsers.nijisanji_parser import parse_member_items
#filtersのitem_filterからbuild_item_label, build_sort_key, detect_sale_status, should_include_item関数をインポート
from filters.item_filter import (
    build_item_label,
    build_sort_key,
    detect_sale_status,
    should_include_item,
)
#dbからデータベース操作に関する関数をインポート
from db import (
    connect_db,
    get_item_by_url,
    init_db,
    insert_item,
    link_item_member,
    mark_notification_sent,
    update_item_snapshot,
)
#notifiersのdiscord_notifierからbuild_discord_messageとsend_discord_message関数をインポート
from notifiers.discord_notifier import build_discord_message, send_discord_message


def main() -> None:
    #env_settingsにload_env_settings関数の返り値を代入
    env_settings = load_env_settings()
    #
    db_path = env_settings["DATABASE_PATH"]
    #
    webhook_url = env_settings["DISCORD_WEBHOOK_URL"]
    #connにconnect_db関数の返り値を代入（引数はdb_path）
    conn = connect_db(db_path)
    #init_db関数を呼び出す（引数はconn）
    init_db(conn)
    #membersにload_members関数の返り値を代入
    members = load_members()
    #sessionにcreate_session関数の返り値を代入
    session = create_session()
    #
    new_items_summary: list[tuple[str, tuple[int, int, int], str, str, str]] = []
    #
    current_run_notified: dict[str, str] = {}
    #
    failed_members: list[tuple[str, str]] = []

    for member in members:  #for文でmembersの各要素をmemberに代入しながら繰り返す
        member_name = member["display_name"]    #memberから"display_name"を取り出してmember_nameに代入
        store_url = member["store_url"] #memberから"store_url"を取り出してstore_urlに代入

        print("=" * 60) #
        print(f"対象: {member_name}")   #
        print(f"URL: {store_url}")  #

        try:    #失敗するまで繰り返す
            html = fetch_html(session, store_url)   #fetch_html関数を呼び出して、引数にsessionとstore_urlを渡し、その返り値をhtmlに代入
        except requests.RequestException as e:  #
            print(f"取得失敗: {member_name}")   #
            print(f"理由: {e}") #
            failed_members.append((member_name, str(e)))    #
            continue    #繰り返す
        
        items = parse_member_items(
            html=html,
            base_url=store_url,
            member_name=member_name,
        )   #parse_member_items関数を呼び出して、引数にhtml、base_url=store_url、member_nameを渡し、その返り値をitemsに代入

        filtered_items = [item for item in items if should_include_item(item)]     #リストを用意しitemsからitemを一つずつ取り出してshould_include_item関数に渡し、Trueを返すものだけをfiltered_itemsに代入

        print(f"抽出件数: {len(items)}")    #
        print(f"フィルタ後件数: {len(filtered_items)}")   #

        for order_index, item in enumerate(filtered_items):     ## 何番目かを示すorder_indexとitemを同時に取り出しながら繰り返す
            label = build_item_label(item)      #build_item_label関数を呼び出して、引数にitemを渡し、その返り値をlabelに代入
            sort_key = build_sort_key(item, order_index)    #build_sort_key関数を呼び出して、引数にitemとorder_indexを渡し、その返り値をsort_keyに代入
            sale_status = detect_sale_status(item)   #detect_sale_status関数を呼び出して、引数にitemを渡し、その返り値をsale_statusに代入
            now_str = datetime.now().isoformat(timespec="seconds")  ## 現在時刻を文字列で取得

            existing_item = get_item_by_url(conn, item.url)     #get_item_by_url関数を呼び出して、引数にconnとitem.urlを渡し、その返り値をexisting_itemに代入

            if existing_item is None:   #
                item_id = insert_item(
                    conn,
                    title=item.title,
                    url=item.url,
                    raw_text=item.raw_text,
                    source_type=item.source_type,
                    current_status=sale_status,
                    first_seen_at=now_str,
                    last_seen_at=now_str,
                )    #insert_item関数を呼び出して、引数にconn、title=item.title、url=item.url、raw_text=item.raw_text、source_type=item.source_type、current_status=sale_status、first_seen_at=now_str、last_seen_at=now_strを渡し、その返り値をitem_idに代入
                link_item_member(conn, item_id=item_id, member_name=item.member_name)     #link_item_member関数を呼び出して、引数にconn、item_id=item_id、member_name=item.member_nameを渡す

                if sale_status in ("upcoming", "on_sale"):  #
                    mark_notification_sent(conn, item_id=item_id, sale_status=sale_status)      #mark_notification_sent関数を呼び出して、引数にconn、item_id=item_id、sale_status=sale_statusを渡す
                    current_run_notified[item.url] = sale_status    #
                    new_items_summary.append(
                        (item.member_name, sort_key, label, item.title, item.url)
                    )   #new_items_summaryに(item.member_name, sort_key, label, item.title, item.url)を追加
                continue    #

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