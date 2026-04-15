import requests


def fetch_shopify_products(session: requests.Session, store_url: str) -> list[dict]:
    """
    Shopifyストアのproducts.json APIから商品一覧を取得する。
    store_url は collections/メンバー名 形式のURL。
    """
    # URLの末尾スラッシュを除いて /products.json を追加
    base = store_url.rstrip("/")
    api_url = f"{base}/products.json?limit=250"

    response = session.get(api_url, timeout=(10, 40))
    response.raise_for_status()

    data = response.json()
    return data.get("products", [])


def fetch_shopify_search(session: requests.Session, base_url: str, query: str) -> list[dict]:
    """
    Shopifyストアの全商品からキーワードでフィルタして返す。
    """
    api_url = f"{base_url.rstrip('/')}/collections/all/products.json"
    params = {"limit": 250}

    response = session.get(api_url, params=params, timeout=(10, 40))
    response.raise_for_status()

    all_products = response.json().get("products", [])

    # タイトルにキーワードが含まれるものだけ返す
    return [p for p in all_products if query in p.get("title", "")]