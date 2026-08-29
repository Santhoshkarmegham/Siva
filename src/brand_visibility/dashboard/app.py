from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from brand_visibility.analytics.metrics import brand_summary, kpis, platform_summary
from brand_visibility.config import DATABASE
from brand_visibility.data.demo import make_demo_data
from brand_visibility.data.load import load_csv, save_to_database
from brand_visibility.data.transform import clean_products
from brand_visibility.dashboard.queries import distinct_values, filtered_products

COLORS = ["#6C63FF", "#00BFA6", "#FFB547", "#FF6B6B", "#45A3FF", "#9B7EDE"]


def _card(label: str, value: str) -> None:
    st.metric(label, value)


def _cards(items: list[tuple[str, str]]) -> None:
    for column, (label, value) in zip(st.columns(len(items)), items):
        with column:
            _card(label, value)


def _bar(data, x, y, title, color=None):
    return px.bar(data, x=x, y=y, color=color, title=title, color_discrete_sequence=COLORS)


def _ensure_database() -> Path:
    if DATABASE.exists():
        return DATABASE
    demo = clean_products(make_demo_data())
    save_to_database(demo, DATABASE)
    return DATABASE


def _sidebar(database: Path) -> pd.DataFrame:
    st.sidebar.header("Filters")
    uploaded = st.sidebar.file_uploader("Upload product CSV", type="csv")
    if uploaded is not None:
        try:
            clean = clean_products(load_csv(uploaded))
            save_to_database(clean, database)
            st.sidebar.success(f"Loaded {len(clean):,} clean products")
        except Exception as exc:
            st.sidebar.error(f"Could not load file: {exc}")
    selections = {c: st.sidebar.multiselect(c.replace("_", " ").title(), distinct_values(database, c))
                  for c in ["brand", "platform", "keyword", "price_range"]}
    all_data = filtered_products(database, {**selections, "price": (0, 1e12), "rating": (0, 5), "position": (0, 1e9)})
    if all_data.empty:
        st.sidebar.warning("This category combination has no products.")
        return all_data
    max_price = max(1.0, float(all_data["price"].max()))
    max_position = max(1, int(all_data["position"].max()))
    selections["price"] = st.sidebar.slider("Price", 0.0, max_price, (0.0, max_price))
    selections["rating"] = st.sidebar.slider("Rating", 0.0, 5.0, (0.0, 5.0), .1)
    selections["position"] = st.sidebar.slider("Position", 1, max_position, (1, max_position))
    return filtered_products(database, selections)


def _overview(df: pd.DataFrame) -> None:
    m = kpis(df)
    _cards([("Total Products", f"{m['total_products']:,}"), ("Average Price", f"${m['avg_price']:,.2f}"),
            ("Average Rating", f"{m['avg_rating']:.2f}"), ("Total Reviews", f"{m['total_reviews']:,.0f}")])
    left, right = st.columns(2)
    left.plotly_chart(px.histogram(df, x="price", nbins=35, title="Price Distribution", color_discrete_sequence=COLORS), use_container_width=True)
    right.plotly_chart(_bar(df["keyword"].value_counts().reset_index(), "keyword", "count", "Products per Keyword"), use_container_width=True)
    share = df["platform"].value_counts().reset_index()
    st.plotly_chart(px.pie(share, names="platform", values="count", title="Platform Share", hole=.42, color_discrete_sequence=COLORS), use_container_width=True)


def _brands(df: pd.DataFrame) -> None:
    summary = brand_summary(df)
    top = summary.iloc[0]
    best = summary.sort_values("avg_visibility", ascending=False).iloc[0]
    _cards([("Top Brand", str(top.brand)), ("Total Brands", f"{df.brand.nunique():,}"),
            ("Avg Visibility", f"{df.visibility_score.mean():.2f}"), ("Best Visibility Brand", str(best.brand))])
    c1, c2 = st.columns(2)
    c1.plotly_chart(_bar(summary.head(15), "brand", "products", "Brand vs Product Count"), use_container_width=True)
    c2.plotly_chart(_bar(summary.sort_values("avg_rating", ascending=False).head(15), "brand", "avg_rating", "Brand vs Average Rating"), use_container_width=True)
    st.plotly_chart(_bar(summary.sort_values("top_10", ascending=False).head(15), "brand", "top_10", "Top Brands in Top 10 Positions"), use_container_width=True)


def _pricing(df: pd.DataFrame) -> None:
    m = kpis(df)
    _cards([("Average Price", f"${m['avg_price']:,.2f}"), ("Maximum Price", f"${df.price.max():,.2f}"),
            ("Minimum Price", f"${df.price.min():,.2f}"), ("Discounted Products", f"{m['discounted_pct']:.1f}%")])
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.histogram(df, x="price", nbins=40, title="Price Distribution", color_discrete_sequence=COLORS), use_container_width=True)
    c2.plotly_chart(px.scatter(df, x="price", y="position", color="platform", hover_name="title", title="Price vs Ranking", color_discrete_sequence=COLORS), use_container_width=True)
    c1.plotly_chart(px.scatter(df, x="price", y="rating", color="brand", hover_name="title", title="Price vs Rating", color_discrete_sequence=COLORS), use_container_width=True)
    ranges = df["price_range"].value_counts().reset_index()
    c2.plotly_chart(_bar(ranges, "price_range", "count", "Price Range Distribution"), use_container_width=True)
    st.plotly_chart(_bar(brand_summary(df).head(15), "brand", "avg_discount", "Average Discount by Brand"), use_container_width=True)


def _platforms(df: pd.DataFrame) -> None:
    summary = platform_summary(df)
    best = summary.sort_values("avg_rating", ascending=False).iloc[0]
    cheapest = summary.sort_values("avg_price").iloc[0]
    _cards([("Total Platforms", str(df.platform.nunique())), ("Best Rated", str(best.platform)),
            ("Cheapest", str(cheapest.platform)), ("Most Products", str(summary.iloc[0].platform))])
    c1, c2 = st.columns(2)
    for target, title, container in [("products", "Platform vs Product Count", c1), ("avg_price", "Platform vs Average Price", c2),
                                      ("avg_rating", "Platform vs Average Rating", c1), ("avg_position", "Platform vs Average Position", c2)]:
        container.plotly_chart(_bar(summary, "platform", target, title), use_container_width=True)
    distribution = df.groupby(["platform", "brand"]).size().reset_index(name="products")
    st.plotly_chart(_bar(distribution, "platform", "products", "Brand Distribution per Platform", "brand"), use_container_width=True)


def _visibility(df: pd.DataFrame) -> None:
    m = kpis(df)
    best = df.sort_values("position").iloc[0]
    _cards([("Average Position", f"{m['avg_position']:.1f}"), ("Best Ranked Product", str(best.title)[:28]),
            ("Avg Visibility", f"{m['avg_visibility']:.2f}"), ("Products in Top 10", f"{m['top_10_pct']:.1f}%")])
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.histogram(df, x="position", nbins=30, title="Ranking Distribution", color_discrete_sequence=COLORS), use_container_width=True)
    c2.plotly_chart(px.scatter(df, x="rating", y="position", color="platform", hover_name="title", title="Rating vs Ranking", color_discrete_sequence=COLORS), use_container_width=True)
    c1.plotly_chart(px.scatter(df, x="reviews", y="position", size="visibility_score", color="brand", hover_name="title", title="Reviews vs Ranking", color_discrete_sequence=COLORS), use_container_width=True)
    c2.plotly_chart(_bar(brand_summary(df).head(15), "brand", "avg_visibility", "Visibility Score by Brand"), use_container_width=True)


def _explorer(df: pd.DataFrame) -> None:
    query = st.text_input("Search by product title")
    shown = df[df["title"].str.contains(query, case=False, na=False)] if query else df
    m = kpis(shown)
    _cards([("Filtered Products", f"{len(shown):,}"), ("Average Price", f"${m['avg_price']:,.2f}"), ("Average Rating", f"{m['avg_rating']:.2f}")])
    columns = ["title", "brand", "price", "rating", "reviews", "platform", "position", "discount_pct", "visibility_score"]
    st.dataframe(shown.sort_values(["visibility_score", "rating"], ascending=False)[columns], use_container_width=True, hide_index=True)
    st.download_button("Download filtered CSV", shown.to_csv(index=False), "filtered_products.csv", "text/csv")
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.scatter(shown, x="price", y="rating", color="platform", hover_name="title", title="Rating vs Price", color_discrete_sequence=COLORS), use_container_width=True)
    c2.plotly_chart(px.scatter(shown, x="reviews", y="position", size="visibility_score", color="platform", hover_name="title", title="Reviews vs Ranking", color_discrete_sequence=COLORS), use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Brand Visibility Intelligence", page_icon="📊", layout="wide")
    st.title("Brand Visibility Intelligence Dashboard")
    st.caption("Search ranking, pricing, brand, and platform intelligence")
    database = _ensure_database()
    df = _sidebar(database)
    if df.empty:
        st.warning("No products match the selected filters.")
        return
    tabs = st.tabs(["Overview", "Brand Insights", "Pricing Analysis", "Platform Analysis", "Visibility & Ranking", "Product Explorer"])
    functions = [_overview, _brands, _pricing, _platforms, _visibility, _explorer]
    for tab, render in zip(tabs, functions):
        with tab:
            render(df)


if __name__ == "__main__":
    main()
