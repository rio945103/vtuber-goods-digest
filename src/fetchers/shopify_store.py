import requests
from bs4 import BeautifulSoup
from models import StoreItem


def fetch_shopify_products(session: requests.Session, store_url: str) -> list[dict]:
    """
    Shopifyストアのproducts.json APIから商品一覧を取得する。
    """
    base = store_url.rstrip("/")
    api_url = f"{base}/products.json?limit=250"

    response = session.get(api_url, timeout=(10, 40))
    response.raise_for_status()

    data = response.json()
    return data.get("products", [])


def fetch_shopify_search(session: requests.Session, base_url: str, query: str) -> list[dict]:
    """
    HTMLスクレイピングで商品を取得する（Neo-Porte用）。
    products.json形式のdictのリストを返す（shopify_parserと互換）。
    """
    search_url = f"{base_url.rstrip('/')}/search"
    params = {"q": query, "type": "product"}

    response = session.get(search_url, params=params, timeout=(10, 40))
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    products = []

    for a_tag in soup.select("a[href*='/products/']"):
        href = a_tag.get("href", "")
        title = a_tag.get_text(strip=True)
        if not title or not href:
            continue
        handle = href.split("/products/")[-1].split("?")[0].strip("/")
        if not handle:
            continue
        products.append({
            "title": title,
            "handle": handle,
            "variants": [{"available": True, "price": "0"}],
        })

    return products