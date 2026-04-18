import json
from flask import Flask, render_template, request
from pathlib import Path
from db import connect_db
from settings import load_env_settings

app = Flask(__name__)

env_settings = load_env_settings()

BASE_DIR = Path(__file__).resolve().parent.parent
db_path_raw = env_settings["DATABASE_PATH"]
db_path = str(BASE_DIR / db_path_raw) if not Path(db_path_raw).is_absolute() else db_path_raw

MEMBERS_PATH = BASE_DIR / "config" / "members.json"

AGENCY_LABELS = {
    "nijisanji": "にじさんじ",
    "vspo": "ぶいすぽ",
    "hololive": "ホロライブ",
    "neoporte": "Neo-Porte",
}


def load_members():
    with open(MEMBERS_PATH, encoding="utf-8") as f:
        return json.load(f)["members"]


def build_member_to_agency():
    members = load_members()
    return {m["display_name"]: m["agency"] for m in members}


@app.route("/")
def index():
    selected_agency = request.args.get("agency", "all")
    selected_member = request.args.get("member", "all")

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
    all_items = cursor.fetchall()
    conn.close()

    members_data = load_members()
    member_to_agency = {m["display_name"]: m["agency"] for m in members_data}

    # 商品に事務所とメンバー情報を付与
    items_with_meta = []
    for item in all_items:
        members_str = item[5] or ""
        member_list = [m.strip() for m in members_str.split(",") if m.strip()]
        agency = None
        for m in member_list:
            if m in member_to_agency:
                agency = member_to_agency[m]
                break
        items_with_meta.append({
            "row": item,
            "agency": agency,
            "members": member_list,
        })

    # 絞り込み
    filtered_items = []
    for entry in items_with_meta:
        if selected_agency != "all" and entry["agency"] != selected_agency:
            continue
        if selected_member != "all" and selected_member not in entry["members"]:
            continue
        filtered_items.append(entry["row"])

    # 事務所ごとの件数
    agency_counts = {"all": len(all_items)}
    for key in AGENCY_LABELS.keys():
        agency_counts[key] = 0
    for entry in items_with_meta:
        if entry["agency"] in agency_counts:
            agency_counts[entry["agency"]] += 1

    # 選択中の事務所に所属するメンバーのリスト（チップ表示用）
    if selected_agency == "all":
        visible_members = members_data
    else:
        visible_members = [m for m in members_data if m["agency"] == selected_agency]

    # メンバーごとの件数
    member_counts = {m["display_name"]: 0 for m in members_data}
    for entry in items_with_meta:
        for m in entry["members"]:
            if m in member_counts:
                member_counts[m] += 1

    return render_template(
        "index.html",
        items=filtered_items,
        selected_agency=selected_agency,
        selected_member=selected_member,
        agency_labels=AGENCY_LABELS,
        agency_counts=agency_counts,
        visible_members=visible_members,
        member_counts=member_counts,
    )


if __name__ == "__main__":
    app.run(debug=True)