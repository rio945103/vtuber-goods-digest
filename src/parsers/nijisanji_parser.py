from bs4 import BeautifulSoup
from urllib.parse import urljoin

from models import StoreItem


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def is_product_link_text(text: str) -> bool:
    if not text:
        return False

    # 商品一覧のリンクは価格と税込を含むことが多い
    if "税込" not in text:
        return False

    if "¥" not in text and "円" not in text:
        return False

    ng_words = [
        "ログイン",
        "新規登録",
        "お気に入り",
        "カート",
        "ご利用ガイド",
        "よくある質問",
        "お問い合わせ",
        "ライバーから探す",
        "絞り込み",
        "価格帯",
        "在庫あり",
        "販売終了も含める",
        "適用する",
        "商品一覧",
    ]
    if any(word in text for word in ng_words):
        return False

    return True


def clean_title(text: str) -> str:
    title = normalize_text(text)

    # 先頭の販売状態を消す
    for prefix in ["NEW ", "再販 ", "まもなく販売 "]:
        if title.startswith(prefix):
            title = title[len(prefix):]

    # 価格以降を落とす
    if " ¥" in title:
        title = title.split(" ¥", 1)[0]
    elif "円" in title and "税込" in title:
        # 念のため別形式も少しケア
        title = title.split("税込", 1)[0].strip()

    return normalize_text(title)


def parse_member_items(html: str, base_url: str, member_name: str) -> list[StoreItem]:
    soup = BeautifulSoup(html, "lxml")
    items: list[StoreItem] = []
    seen_urls: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        text = normalize_text(a_tag.get_text(" ", strip=True))

        if not href or not text:
            continue

        # 商品詳細ページだけを通す
        if not href.endswith(".html"):
            continue

        if not is_product_link_text(text):
            continue

        full_url = urljoin(base_url, href)

        if full_url in seen_urls:
            continue

        seen_urls.add(full_url)

        item = StoreItem(
            member_name=member_name,
            title=clean_title(text),
            url=full_url,
            raw_text=text,
            source_type="goods",
        )
        items.append(item)

    return items