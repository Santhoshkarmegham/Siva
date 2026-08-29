from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd

from brand_visibility.config import EXPECTED_COLUMNS, TABLE_NAME

ALIASES = {
    "query": "keyword", "search_term": "keyword", "product_title": "title",
    "name": "title", "extracted_price": "price", "original_price": "raw_price",
    "old_price": "raw_price", "source": "platform", "rank": "position",
    "product_link": "link", "url": "link", "image": "thumbnail",
}


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(c).strip().lower().replace(" ", "_") for c in frame.columns]
    frame = frame.rename(columns={k: v for k, v in ALIASES.items() if k in frame.columns})
    for column in EXPECTED_COLUMNS:
        if column not in frame:
            frame[column] = pd.NA
    return frame


def load_csv(source: str | Path | object) -> pd.DataFrame:
    return normalize_columns(pd.read_csv(source))


def save_to_database(frame: pd.DataFrame, database: str | Path, table: str = TABLE_NAME) -> None:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        frame.to_sql(table, connection, if_exists="replace", index=False)
        connection.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_brand ON "{table}" (brand)')
        connection.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_platform ON "{table}" (platform)')
        connection.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_keyword ON "{table}" (keyword)')


def load_from_database(database: str | Path, table: str = TABLE_NAME) -> pd.DataFrame:
    with sqlite3.connect(database) as connection:
        return pd.read_sql_query(f'SELECT * FROM "{table}"', connection)
