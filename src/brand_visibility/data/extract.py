from __future__ import annotations

import os
import pandas as pd


def fetch_google_shopping(keyword: str, api_key: str | None = None, limit: int = 100) -> pd.DataFrame:
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("Install project requirements to use SerpAPI extraction") from exc
    key = api_key or os.getenv("SERPAPI_KEY")
    if not key:
        raise ValueError("SERPAPI_KEY is required for live extraction")
    response = requests.get(
        "https://serpapi.com/search.json",
        params={"engine": "google_shopping", "q": keyword, "api_key": key,
                "gl": os.getenv("SERPAPI_COUNTRY", "us"),
                "hl": os.getenv("SERPAPI_LANGUAGE", "en")},
        timeout=45,
    )
    response.raise_for_status()
    rows = []
    for item in response.json().get("shopping_results", [])[:limit]:
        rows.append({
            "keyword": keyword, "title": item.get("title"),
            "price": item.get("extracted_price", item.get("price")),
            "raw_price": item.get("extracted_old_price", item.get("old_price")),
            "rating": item.get("rating"), "reviews": item.get("reviews"),
            "platform": item.get("source"), "position": item.get("position"),
            "delivery": item.get("delivery"),
            "link": item.get("product_link", item.get("link")),
            "thumbnail": item.get("thumbnail"),
        })
    return pd.DataFrame(rows)
