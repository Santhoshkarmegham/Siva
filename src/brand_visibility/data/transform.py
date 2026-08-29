from __future__ import annotations

import re
import numpy as np
import pandas as pd

from brand_visibility.config import BRANDS
from brand_visibility.data.load import normalize_columns

INVALID = {"", "na", "n/a", "none", "null", "not available", "many", "-"}


def _number(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.lower().str.strip()
    text = text.mask(text.isin(INVALID))
    multiplier = np.where(text.str.contains("k", na=False), 1_000,
                 np.where(text.str.contains("m", na=False), 1_000_000, 1))
    numeric = pd.to_numeric(text.str.replace(r"[^0-9.\-]", "", regex=True), errors="coerce")
    return numeric * multiplier


def _clean_title(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = re.sub(r"[^\w\s\-&+().'\/]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _brand(title: str) -> str:
    lowered = title.casefold()
    for brand in BRANDS:
        if re.search(rf"\b{re.escape(brand.casefold())}\b", lowered):
            return brand
    first = re.sub(r"[^A-Za-z0-9]", "", title.split()[0]) if title else ""
    return first.title() if 1 < len(first) < 20 else "Other"


def clean_products(raw: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(raw)
    df["title"] = df["title"].map(_clean_title)
    for column in ["price", "raw_price", "rating", "reviews", "position"]:
        df[column] = _number(df[column])
    df["price"] = df["price"].mask(df["price"] <= 0)
    df["raw_price"] = df["raw_price"].mask(df["raw_price"] <= 0).fillna(df["price"])
    df["rating"] = df["rating"].where(df["rating"].between(0, 5))
    df["reviews"] = df["reviews"].where(df["reviews"] >= 0).fillna(0).round().astype("Int64")
    df["position"] = df["position"].where(df["position"] > 0)
    df = df.dropna(subset=["price", "position"]).copy()
    for column in ["keyword", "platform"]:
        df[column] = df[column].astype("string").fillna("Unknown").str.strip().str.title()
    df["delivery"] = df["delivery"].astype("string").fillna("Unknown").str.strip().replace("", "Unknown")
    df["brand"] = df["title"].map(_brand)
    df["visibility_score"] = (100 / df["position"]).clip(0, 100).round(2)
    bins = [-np.inf, 50, 150, 500, 1000, np.inf]
    labels = ["Budget", "Economy", "Mid-range", "Premium", "Luxury"]
    df["price_range"] = pd.cut(df["price"], bins=bins, labels=labels).astype("string")
    df["discount_pct"] = np.where(
        df["raw_price"] > df["price"],
        ((df["raw_price"] - df["price"]) / df["raw_price"] * 100), 0,
    ).round(2)
    df = df.drop_duplicates(subset=["keyword", "title", "platform", "price"])
    upper = df["price"].quantile(0.995) if len(df) >= 20 else df["price"].max()
    df["price"] = df["price"].clip(upper=upper)
    return df.reset_index(drop=True)
