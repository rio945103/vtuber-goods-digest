from models import StoreItem


EXCLUDE_WORDS = [
    "メンテ",
    "障害",
    "決済",
    "送料",
    "配送",
    "遅延",
    "システム",
    "在庫なし",
    "SOLD OUT",
    "売り切れ",
]


def _combined_text(item: StoreItem) -> str:
    return f"{item.title} {item.raw_text}"


def should_include_item(item: StoreItem) -> bool:
    text = _combined_text(item)

    if "【常設】" in text:
        return False

    if any(word in text for word in EXCLUDE_WORDS):
        return False

    return True


def detect_item_category(item: StoreItem) -> str:
    text = _combined_text(item)

    if "ボイス" in text or "dig-" in item.url:
        return "ボイス"

    return "グッズ"


def detect_status_tags(item: StoreItem) -> list[str]:
    text = _combined_text(item)
    tags: list[str] = []

    if "NEW" in text:
        tags.append("NEW")

    if "再販" in text:
        tags.append("再販")

    if "まもなく販売" in text:
        tags.append("まもなく販売")

    return tags


def build_item_label(item: StoreItem) -> str:
    parts = detect_status_tags(item)
    parts.append(detect_item_category(item))
    return "[" + " / ".join(parts) + "]"


def build_sort_key(item: StoreItem, order_index: int) -> tuple[int, int, int]:
    text = _combined_text(item)
    category = detect_item_category(item)

    if "NEW" in text:
        status_priority = 0
    elif "再販" in text:
        status_priority = 1
    elif "まもなく販売" in text:
        status_priority = 2
    else:
        status_priority = 3

    if category == "グッズ":
        category_priority = 0
    else:
        category_priority = 1

    return (status_priority, category_priority, order_index)