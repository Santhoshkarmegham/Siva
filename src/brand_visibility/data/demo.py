from __future__ import annotations

import numpy as np
import pandas as pd


def make_demo_data(rows: int = 240, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    brands = ["Apple", "Samsung", "Sony", "Dell", "HP", "Lenovo", "Asus", "Nike", "Adidas", "Puma"]
    keywords = ["Laptop", "Smartphone", "Headphones", "Running Shoes"]
    platforms = ["Amazon", "Walmart", "Best Buy", "eBay"]
    records = []
    for i in range(rows):
        brand = rng.choice(brands)
        keyword = rng.choice(keywords)
        price = round(float(rng.lognormal(4.7, 0.75)), 2)
        discount = float(rng.choice([0, 0, 0, 5, 10, 15, 20, 30]))
        records.append({
            "keyword": keyword, "title": f"{brand} {keyword} Model {i + 1}", "price": price,
            "raw_price": round(price / (1 - discount / 100), 2) if discount else price,
            "rating": round(float(np.clip(rng.normal(4.1, .45), 1, 5)), 1),
            "reviews": int(rng.lognormal(6, 1.5)), "platform": rng.choice(platforms),
            "position": int(rng.integers(1, 61)), "delivery": rng.choice(["Free delivery", "Paid", "Prime"]),
            "link": "", "thumbnail": "",
        })
    return pd.DataFrame(records)
