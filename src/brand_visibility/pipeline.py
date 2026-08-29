from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd
try:
    from dotenv import load_dotenv
except ImportError:  # The pipeline still works when no .env file is needed.
    def load_dotenv() -> bool:
        return False

from brand_visibility.analytics.eda import generate_eda_report
from brand_visibility.config import CLEAN_CSV, DATABASE, DEFAULT_CSV, PROCESSED_DIR
from brand_visibility.data.demo import make_demo_data
from brand_visibility.data.extract import fetch_google_shopping
from brand_visibility.data.load import load_csv, save_to_database
from brand_visibility.data.transform import clean_products


def run(csv: Path | None, keywords: list[str], demo: bool = False) -> pd.DataFrame:
    load_dotenv()
    frames = []
    if csv and csv.exists():
        frames.append(load_csv(csv))
    if demo:
        frames.append(make_demo_data())
    frames.extend(fetch_google_shopping(word) for word in keywords)
    if not frames:
        raise FileNotFoundError(f"No input data. Add {DEFAULT_CSV}, pass --csv, --keywords, or --demo.")
    clean = clean_products(pd.concat(frames, ignore_index=True))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(CLEAN_CSV, index=False)
    save_to_database(clean, DATABASE)
    (PROCESSED_DIR / "eda_summary.json").write_text(json.dumps(generate_eda_report(clean), indent=2, default=str))
    return clean


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Brand Visibility dataset and SQLite database")
    parser.add_argument("--csv", type=Path, default=None)
    parser.add_argument("--keywords", nargs="*", default=[])
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    result = run(args.csv, args.keywords, args.demo)
    print(f"Processed {len(result):,} products -> {CLEAN_CSV}")


if __name__ == "__main__":
    main()
