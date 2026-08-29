from __future__ import annotations

import pandas as pd


def kpis(df: pd.DataFrame) -> dict[str, float | int]:
    return {
        "total_products": len(df), "avg_price": df["price"].mean(),
        "avg_rating": df["rating"].mean(), "total_reviews": df["reviews"].sum(),
        "avg_position": df["position"].mean(), "avg_visibility": df["visibility_score"].mean(),
        "discounted_pct": (df["discount_pct"] > 0).mean() * 100,
        "top_10_pct": (df["position"] <= 10).mean() * 100,
    }


def brand_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("brand", as_index=False).agg(
        products=("title", "count"), avg_price=("price", "mean"),
        avg_rating=("rating", "mean"), avg_position=("position", "mean"),
        avg_visibility=("visibility_score", "mean"), avg_discount=("discount_pct", "mean"),
        top_10=("position", lambda x: int((x <= 10).sum())),
    ).sort_values("products", ascending=False))


def platform_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("platform", as_index=False).agg(
        products=("title", "count"), avg_price=("price", "mean"),
        avg_rating=("rating", "mean"), avg_position=("position", "mean"),
        avg_discount=("discount_pct", "mean"),
    ).sort_values("products", ascending=False))
