from urllib.parse import urljoin
from models import StoreItem


def parse_shopify_products(
    products: list[dict],
    base_url: str,
    member_name: str,
) -> list[StoreItem]:
    """
    Shopify products.json の商品リストをStoreItemに変換する。
    """
    items: list[StoreItem] = []
    seen_urls: set[str] = set()

    for product in products:
        title = product.get("title", "").strip()
        handle = product.get("handle", "").strip()

        if not title or not handle:
            continue

        # 商品URLを組み立てる
        # base_urlからドメイン部分だけ取り出す
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        full_url = f"{domain}/products/{handle}"

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # 価格情報を取得（最初のvariantの価格）
        variants = product.get("variants", [])
        price_str = ""
        if variants:
            price = variants[0].get("price", "")
            if price:
                price_str = f"¥{int(float(price)):,}"

        raw_text = f"{title} {price_str}".strip()

        item = StoreItem(
            member_name=member_name,
            title=title,
            url=full_url,
            raw_text=raw_text,
            source_type="goods",
        )
        items.append(item)

    return items