import requests


def fetch_shopify_products(session: requests.Session, store_url: str) -> list[dict]:
    base = store_url.rstrip("/")
    api_url = f"{base}/products.json?limit=250"

    response = session.get(api_url, timeout=(10, 40))
    response.raise_for_status()

    data = response.json()
    return data.get("products", [])


def fetch_shopify_search(session: requests.Session, base_url: str, query: str) -> list[dict]:
    from urllib.parse import quote, urlparse
    from bs4 import BeautifulSoup

    url = f"{base_url.rstrip('/')}/search?q={quote(query)}&type=product"
    response = session.get(url, timeout=(10, 40))
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    products = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        if "/products/" not in href:
            continue

        span = a_tag.find("span", class_="prod-title")
        if not span:
            continue

        title = span.get_text(strip=True)
        if not title:
            continue

        full_url = domain + href.split("?")[0]
        handle = href.split("/products/")[-1].split("?")[0]

        products.append({
            "title": title,
            "handle": handle,
            "variants": [],
        })

    return products
