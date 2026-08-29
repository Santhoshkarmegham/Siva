from __future__ import annotations

import pandas as pd
from brand_visibility.analytics.metrics import brand_summary, platform_summary, kpis


def generate_eda_report(df: pd.DataFrame) -> dict:
    """Return reusable answers for the main EDA groups in the project brief."""
    corr_cols = ["price", "rating", "reviews", "position", "discount_pct", "visibility_score"]
    return {
        "market_kpis": kpis(df),
        "products_per_keyword": df["keyword"].value_counts().to_dict(),
        "price_distribution": df["price"].describe().to_dict(),
        "brand_summary": brand_summary(df).to_dict("records"),
        "platform_summary": platform_summary(df).to_dict("records"),
        "correlations": df[corr_cols].corr(numeric_only=True).round(3).to_dict(),
        "highest_price_per_keyword": df.loc[df.groupby("keyword")["price"].idxmax(), ["keyword", "title", "price"]].to_dict("records"),
        "top_visibility_products": df.nlargest(10, "visibility_score")[["title", "brand", "visibility_score"]].to_dict("records"),
    }
