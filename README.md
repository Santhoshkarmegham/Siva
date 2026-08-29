# Brand Visibility Intelligence Dashboard

Complete Python/Streamlit implementation of the Brand Visibility Intelligence project.

## Features

- Loads a dirty CSV and optionally appends Google Shopping results from SerpAPI
- Cleans prices, ratings, reviews, rankings, delivery values, titles, and platform names
- Derives `brand`, `visibility_score`, `price_range`, and `discount_pct`
- Stores the clean data in SQLite
- Provides SQL-backed sidebar filters and six interactive dashboard tabs
- Includes reusable EDA helpers and a command-line pipeline

## Quick start

```bash
make setup
make demo
make run
```

Run `make help` to see all scaffold, pipeline, validation, and cleanup commands.

### Windows PowerShell

Windows normally does not include `make`. From PowerShell, use the included native
script instead:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\project.ps1 setup
.\project.ps1 demo
.\project.ps1 run
```

For your real CSV:

```powershell
Copy-Item "C:\path\to\brand_dataset.csv" "data\raw\brand_dataset.csv"
.\project.ps1 pipeline -Csv "data\raw\brand_dataset.csv"
.\project.ps1 run
```

The execution-policy command affects only the current PowerShell window. You can
also run a single command without changing the session policy:

```powershell
powershell -ExecutionPolicy Bypass -File .\project.ps1 setup
```

To use your CSV:

```bash
make pipeline CSV=data/raw/brand_dataset.csv
make run
```

To include live API data, copy `.env.example` to `.env`, add a SerpAPI key, and run:

```bash
python -m brand_visibility.pipeline --csv data/raw/brand_dataset.csv --keywords laptop shoes
```

The pipeline writes `data/processed/brand_visibility_clean.csv` and
`data/processed/brand_visibility.db`. The dashboard can also upload a CSV directly.

## Expected CSV columns

`keyword`, `title`, `price`, `raw_price`, `rating`, `reviews`, `platform`,
`position`, `delivery`, `link`, and `thumbnail`. Column matching is case-insensitive,
and common names such as `source`, `extracted_price`, and `product_link` are accepted.

## Project structure

```text
BrandVisibility/
├── app.py
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
└── src/brand_visibility/
    ├── analytics/
    ├── dashboard/
    └── data/
```
