from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd


def distinct_values(database: Path, column: str) -> list[str]:
    allowed = {"brand", "platform", "keyword", "price_range"}
    if column not in allowed:
        raise ValueError("Unsupported filter column")
    with sqlite3.connect(database) as connection:
        rows = connection.execute(f'SELECT DISTINCT "{column}" FROM products WHERE "{column}" IS NOT NULL ORDER BY 1').fetchall()
    return [str(row[0]) for row in rows]


def filtered_products(database: Path, filters: dict) -> pd.DataFrame:
    clauses, params = [], []
    for column in ["brand", "platform", "keyword", "price_range"]:
        values = filters.get(column) or []
        if values:
            clauses.append(f'"{column}" IN ({",".join("?" for _ in values)})')
            params.extend(values)
    for column, key in [("price", "price"), ("rating", "rating"), ("position", "position")]:
        low, high = filters[key]
        clauses.append(f'"{column}" BETWEEN ? AND ?')
        params.extend([low, high])
    sql = "SELECT * FROM products" + (" WHERE " + " AND ".join(clauses) if clauses else "")
    with sqlite3.connect(database) as connection:
        return pd.read_sql_query(sql, connection, params=params)
