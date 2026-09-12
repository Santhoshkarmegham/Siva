# Brand Visibility Intelligence Dashboard

An end-to-end e-commerce analytics project that collects product search data from a CSV file and/or Google Shopping through SerpAPI, cleans and enriches the data, stores it in SQLite, performs exploratory analysis, and presents the results in an interactive Streamlit dashboard.

## Table of contents

1. [Project objective](#project-objective)
2. [Business questions](#business-questions)
3. [Technology stack](#technology-stack)
4. [Architecture and data flow](#architecture-and-data-flow)
5. [Project structure](#project-structure)
6. [Explanation of every file](#explanation-of-every-file)
7. [Input data](#input-data)
8. [Cleaning and feature engineering](#cleaning-and-feature-engineering)
9. [Pipeline execution modes](#pipeline-execution-modes)
10. [Installation and setup](#installation-and-setup)
11. [How to run the project](#how-to-run-the-project)
12. [Dashboard guide](#dashboard-guide)
13. [Generated outputs](#generated-outputs)
14. [Common errors](#common-errors)
15. [Possible improvements](#possible-improvements)

## Project objective

Shopping search results reveal which brands appear most often, which products receive the best rankings, how prices vary by platform, and whether ratings, reviews, or discounts are associated with visibility.

This project converts those results into business intelligence. It aims to:

- combine product records from a supplied CSV and live API searches;
- repair noisy, missing, or inconsistent values;
- calculate brand, discount, price-range, and visibility features;
- persist one clean dataset in CSV and SQLite formats;
- answer market, brand, pricing, platform, and ranking questions;
- provide interactive filters and charts in Streamlit.

## Business questions

- How many products are available for each keyword?
- Which brands appear most frequently?
- Which brands have the strongest average visibility?
- Which brands appear most often in the top ten?
- What is the average price and rating by platform?
- Which platform has the most products or lowest average price?
- What percentage of products are discounted?
- Do price, rating, reviews, or discounts relate to ranking?
- Which products have the highest visibility scores?

## Technology stack

| Technology | Why it is used |
|---|---|
| Python 3.10+ | Main language and pipeline orchestration |
| Pandas | CSV loading, merging, cleaning, and aggregation |
| NumPy | Numeric transformations, conditions, demo generation, and price bins |
| Requests | Calling the SerpAPI HTTP endpoint |
| python-dotenv | Loading API settings from `.env` |
| SQLite | Storing clean products and applying dashboard filters |
| Plotly | Interactive charts |
| Streamlit | Dashboard, filters, table, search, and downloads |
| setuptools | Installing `brand_visibility` as a Python package |

## Architecture and data flow

```text
Raw CSV                       Google Shopping SerpAPI
   |                                    |
   +------------ load/extract ----------+
                    |
             Pandas DataFrames
                    |
            concatenate all rows
                    |
       clean and standardize columns
                    |
            feature engineering
                    |
      +-------------+--------------+
      |             |              |
 Clean CSV      SQLite table    EDA JSON
      |             |              |
      +-------------+--------------+
                    |
          Streamlit dashboard
                    |
       KPIs, filters, charts, table
```

The pipeline is separate from the dashboard. Repeatable preparation happens once in the pipeline; the dashboard reads prepared SQLite records and focuses on filtering and visualization.

## Project structure

```text
BrandVisibility/
├── app.py
├── Makefile
├── pyproject.toml
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── data/
│   ├── raw/
│   │   └── brand_visibility.csv
│   └── processed/
│       ├── brand_visibility_clean.csv     # generated
│       ├── brand_visibility.db            # generated
│       └── eda_summary.json               # generated
├── src/brand_visibility/
│   ├── __init__.py
│   ├── config.py
│   ├── pipeline.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── load.py
│   │   ├── extract.py
│   │   ├── transform.py
│   │   └── demo.py
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   └── eda.py
│   └── dashboard/
│       ├── __init__.py
│       ├── queries.py
│       └── app.py
└── tests/
    └── __init__.py
```

Files in `data/processed/` are created or replaced by the pipeline and should not be edited manually.

## Explanation of every file

### Root files

#### `app.py`

The Streamlit entry point. It adds `src` to Python's import path and calls the dashboard `main()` function:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from brand_visibility.dashboard.app import main
```

Keeping it small leaves the real dashboard implementation inside the installable package.

#### `pyproject.toml`

Defines the package name and version, Python 3.10+ requirement, dependencies, and `src`-layout discovery. `python -m pip install -e .` reads this file. Editable installation means local code changes become available without reinstalling.

#### `requirements.txt`

Lists the runtime libraries in the conventional pip format. It is useful for services that expect this filename. For local development, `python -m pip install -e .` is preferred because it installs dependencies and the package itself.

#### `.env.example`

A safe template for live API settings:

```env
SERPAPI_KEY=replace_with_your_key
SERPAPI_COUNTRY=us
SERPAPI_LANGUAGE=en
```

Copy it to `.env` and insert a real key. `.env` is excluded from Git to protect credentials.

#### `.gitignore`

Excludes virtual environments, secrets, Python caches, generated databases, and processed data from source control.

#### `Makefile`

Optional shortcuts for systems with GNU Make:

| Command | Purpose |
|---|---|
| `make scaffold` | Create folders and package marker files |
| `make setup` | Create `.venv` and install the project |
| `make demo` | Generate demo outputs |
| `make pipeline CSV=path` | Process a specified CSV |
| `make run` | Start Streamlit |
| `make check` | Compile the source and test a demo pipeline run |
| `make tree` | Display the project structure |
| `make clean` | Remove Python/build caches |
| `make clean-data` | Remove generated data outputs |

Make is optional; all operations can be run directly with Python.

### Package-level files

#### `src/brand_visibility/__init__.py`

Marks the directory as a Python package and exposes version `1.0.0`.

#### `src/brand_visibility/config.py`

Centralizes paths and constants instead of hardcoding them throughout the project. It defines raw/processed directories, output files, the SQLite table name, expected source columns, and the brand dictionary used during extraction from titles.

#### `src/brand_visibility/pipeline.py`

Coordinates the ETL process—Extract, Transform, and Load. Its `run()` function:

1. loads `.env`;
2. loads a CSV when `--csv` is provided;
3. generates sample rows when `--demo` is provided;
4. calls SerpAPI for every `--keywords` value;
5. concatenates all available DataFrames;
6. cleans and enriches the combined rows;
7. writes the clean CSV;
8. replaces the SQLite `products` table;
9. writes the EDA JSON.

CSV and API records share the same cleaning rules because they are combined before transformation:

```python
clean = clean_products(pd.concat(frames, ignore_index=True))
```

### Data package

#### `src/brand_visibility/data/load.py`

Handles column normalization, CSV reading, and SQLite persistence.

`normalize_columns()` converts headings to lowercase snake case and supports common aliases:

| Incoming name | Standard name |
|---|---|
| `query`, `search_term` | `keyword` |
| `product_title`, `name` | `title` |
| `extracted_price` | `price` |
| `original_price`, `old_price` | `raw_price` |
| `source` | `platform` |
| `rank` | `position` |
| `product_link`, `url` | `link` |
| `image` | `thumbnail` |

Missing expected columns are added as null values. `save_to_database()` replaces the SQLite `products` table and adds indexes for brand, platform, and keyword. `load_from_database()` reads it back for validation or analysis.

#### `src/brand_visibility/data/extract.py`

Contains the live API function:

```python
fetch_google_shopping(keyword, api_key=None, limit=100)
```

It sends a GET request to `https://serpapi.com/search.json` with `engine=google_shopping`, keyword, country, language, and API key. It checks HTTP errors, reads `shopping_results`, maps SerpAPI fields to the project schema, and returns a DataFrame.

No live request occurs unless `--keywords` is supplied.

#### `src/brand_visibility/data/transform.py`

Contains `clean_products()`, the main cleaning and feature-engineering function. It:

- removes currency symbols and noise from numeric values;
- converts `2.5K` and `1.2M` to `2500` and `1200000`;
- treats `Not Available`, `many`, `null`, and `-` as missing;
- rejects non-positive prices and positions;
- keeps only ratings between 0 and 5;
- replaces missing or negative reviews with zero;
- cleans product titles;
- standardizes keyword and platform capitalization;
- fills missing delivery values with `Unknown`;
- extracts a brand from the title;
- calculates visibility, price range, and discount;
- removes duplicate products;
- caps extreme prices at the 99.5th percentile when at least 20 rows exist.

#### `src/brand_visibility/data/demo.py`

Generates 240 reproducible product records by default. A fixed random seed makes repeated demo runs consistent. Demo mode allows development without a real CSV or paid API request.

### Analytics package

#### `src/brand_visibility/analytics/metrics.py`

Defines reusable business calculations:

- `kpis()` calculates product count, average price/rating/position/visibility, total reviews, discounted percentage, and top-ten percentage;
- `brand_summary()` calculates product, price, rating, ranking, visibility, discount, and top-ten measures by brand;
- `platform_summary()` calculates related measures by platform.

Separating these definitions from the UI avoids inconsistent calculations between tabs.

#### `src/brand_visibility/analytics/eda.py`

Builds a serializable report containing market KPIs, products per keyword, descriptive price statistics, brand/platform summaries, correlations, highest-priced product per keyword, and the ten highest-visibility products.

### Dashboard package

#### `src/brand_visibility/dashboard/queries.py`

Provides the SQLite query layer. `distinct_values()` supplies sidebar choices. `filtered_products()` builds dynamic parameterized SQL from categorical selections and numeric ranges:

```sql
SELECT * FROM products
WHERE brand IN (?, ?)
  AND price BETWEEN ? AND ?
  AND rating BETWEEN ? AND ?
  AND position BETWEEN ? AND ?;
```

Parameters are passed separately, which is safer than inserting selected values directly into SQL.

#### `src/brand_visibility/dashboard/app.py`

Implements the Streamlit interface. It configures the page, creates demo data when no database exists, accepts CSV uploads, cleans uploaded data, creates filters, renders six dashboard tabs, and provides charts, searchable records, and CSV download.

#### Package `__init__.py` files

These files mark folders as importable Python packages. Some re-export commonly used functions for shorter imports.

### Data and test folders

#### `data/raw/`

Stores source data exactly as received. Do not manually clean it; retaining the original makes processing reproducible. The repository currently uses `data/raw/brand_visibility.csv`. Any filename works when supplied explicitly with `--csv`.

#### `data/processed/`

Stores generated clean data, the database, and EDA summary. A new pipeline run replaces these outputs.

#### `tests/`

Reserved for automated tests. Future tests should cover cleaning edge cases, API mapping, SQL filters, and KPI calculations.

## Input data

| Column | Clean type | Meaning |
|---|---|---|
| `keyword` | text | Search term used to obtain the product |
| `title` | text | Product name |
| `price` | float | Current selling price |
| `raw_price` | float | Original price before discount |
| `rating` | float | Rating from 0 to 5 |
| `reviews` | integer | Customer-review count |
| `platform` | text | Marketplace or seller source |
| `position` | numeric | Position in shopping results |
| `delivery` | text | Delivery description |
| `link` | URL/text | Product page link |
| `thumbnail` | URL/text | Product image URL |

Column matching is case-insensitive after surrounding spaces are removed and spaces are changed to underscores.

## Cleaning and feature engineering

### Numeric conversion

```text
$1,299.99  -> 1299.99
2.5K       -> 2500
1.2M       -> 1200000
many       -> missing
```

### Brand extraction

Titles are compared with the brand list in `config.py`:

```text
Apple iPhone 16 Pro -> Apple
Samsung Galaxy S25  -> Samsung
```

If no known brand matches, the first reasonable title word is used; otherwise the result is `Other`.

### Visibility score

```python
visibility_score = 100 / position
```

| Position | Score |
|---:|---:|
| 1 | 100.00 |
| 2 | 50.00 |
| 5 | 20.00 |
| 10 | 10.00 |
| 50 | 2.00 |

A smaller position is a better search rank and therefore produces higher visibility.

### Price range

| Category | Rule |
|---|---|
| Budget | price <= 50 |
| Economy | 50 < price <= 150 |
| Mid-range | 150 < price <= 500 |
| Premium | 500 < price <= 1000 |
| Luxury | price > 1000 |

These thresholds assume one dollar-based market. Adjust the bins in `transform.py` for other currencies or markets.

### Discount percentage

```python
discount_pct = ((raw_price - price) / raw_price) * 100
```

The result is zero when there is no valid price reduction.

### Duplicate definition

A row is considered duplicated when `keyword + title + platform + price` matches another row. This avoids inflated counts while allowing the same product to appear for a different keyword or price.

## Pipeline execution modes

### CSV only

```bash
python -m brand_visibility.pipeline --csv "data/raw/brand_visibility.csv"
```

No API request is made.

### Demo only

```bash
python -m brand_visibility.pipeline --demo
```

Requires neither CSV nor API key.

### API only

```bash
python -m brand_visibility.pipeline --keywords laptop smartphone headphones
```

Calls SerpAPI once for each keyword.

### CSV and API combined

```bash
python -m brand_visibility.pipeline --csv "data/raw/brand_visibility.csv" --keywords laptop smartphone
```

API rows are appended to CSV rows before common cleaning.

### Demo and API combined

```bash
python -m brand_visibility.pipeline --demo --keywords laptop
```

Useful when testing API integration while retaining enough dashboard data.

## Installation and setup

### Prerequisites

- Python 3.10 or newer;
- pip;
- Git when cloning;
- a SerpAPI key only for live API mode.

Check the tools:

```bash
python --version
python -m pip --version
```

Clone and enter the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd BrandVisibility
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it using the command appropriate to your operating system and terminal, then install:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Confirm package installation:

```bash
python -c "import brand_visibility; print(brand_visibility.__version__)"
```

Expected output: `1.0.0`.

### Configure live API access

Create `.env` in the repository root using `.env.example` as the template:

```env
SERPAPI_KEY=your_real_serpapi_key
SERPAPI_COUNTRY=us
SERPAPI_LANGUAGE=en
```

Never commit the real key.

## How to run the project

### Fastest first run

```bash
python -m brand_visibility.pipeline --demo
streamlit run app.py
```

Open the address printed by Streamlit, normally `http://localhost:8501`.

### Run with the current CSV

```bash
python -m brand_visibility.pipeline --csv "data/raw/brand_visibility.csv"
streamlit run app.py
```

### Run with another CSV

```bash
python -m brand_visibility.pipeline --csv "/full/path/to/your_file.csv"
streamlit run app.py
```

### Run CSV and API together

```bash
python -m brand_visibility.pipeline --csv "data/raw/brand_visibility.csv" --keywords laptop smartphone
streamlit run app.py
```

Stop Streamlit with `Ctrl+C`. Dependencies do not need to be reinstalled on later runs. Rerun the pipeline when the raw data or API keywords change.

## Dashboard guide

### Sidebar

Filters every tab using SQL:

- brand;
- platform;
- keyword;
- price-range category;
- numeric price range;
- rating range;
- ranking/position range.

The sidebar can also upload a CSV. Uploaded records are cleaned and replace the current SQLite table.

### Overview

Total products, average price, average rating, total reviews, price distribution, products per keyword, and platform share.

### Brand Insights

Top brand, brand count, average visibility, best-visibility brand, products and ratings by brand, and brands appearing in the top ten.

### Pricing Analysis

Average/minimum/maximum prices, discounted percentage, price distribution, price versus ranking/rating, price-range counts, and average discount by brand.

### Platform Analysis

Platform count, best-rated and cheapest platforms, platform with the most products, and count/price/rating/position/brand comparisons.

### Visibility & Ranking

Average position, best-ranked product, average visibility, top-ten percentage, ranking distribution, rating/reviews versus ranking, and visibility by brand.

### Product Explorer

Title search, filtered KPIs, sortable table, CSV download, rating-versus-price chart, and reviews-versus-ranking bubble chart.

## Generated outputs

### `data/processed/brand_visibility_clean.csv`

Clean dataset for inspection, spreadsheet analysis, submission, or another BI tool.

### `data/processed/brand_visibility.db`

SQLite database containing the `products` table used by Streamlit. Each pipeline run replaces the table.

### `data/processed/eda_summary.json`

Machine-readable KPIs, distributions, grouped results, correlations, highest-priced products, and high-visibility products.

## Common errors

### `No module named 'brand_visibility'`

Install the package in the active environment:

```bash
python -m pip install -e .
```

Check that Python and pip refer to the same environment:

```bash
python -c "import sys; print(sys.executable)"
python -m pip --version
```

### `No input data`

The specified CSV does not exist and no demo/API source was provided. The current repository filename is:

```text
data/raw/brand_visibility.csv
```

Use its actual path:

```bash
python -m brand_visibility.pipeline --csv "data/raw/brand_visibility.csv"
```

### `SERPAPI_KEY is required for live extraction`

`--keywords` requests live data, but `.env` is missing or has a placeholder. Add a valid key or omit `--keywords`.

### SerpAPI HTTP error

Possible causes are an invalid key, exhausted quota, unavailable network, rate limit, or temporary service failure. Run CSV-only mode to confirm the rest of the pipeline works.

### CSV parsing or encoding error

Confirm the input is a genuine comma-separated file. If it uses another encoding or delimiter, update `load_csv()` in `data/load.py`, for example:

```python
pd.read_csv(source, encoding="latin-1")
pd.read_csv(source, sep=";")
```

Only use options that match the actual source file.

### Dashboard unexpectedly uses demo data

When the database is absent, the dashboard creates demo data so the UI remains usable. Run the real pipeline before Streamlit to replace it.

### Filters return no products

The selections have no intersection. Clear categories or widen numeric ranges.

### Port 8501 is already occupied

```bash
streamlit run app.py --server.port 8502
```

## Validation commands

Check Python syntax:

```bash
python -m compileall -q src app.py
```

Run a reproducible pipeline test:

```bash
python -m brand_visibility.pipeline --demo
```

Inspect the database:

```bash
python -c "from brand_visibility.config import DATABASE; from brand_visibility.data.load import load_from_database; data=load_from_database(DATABASE); print(data.shape); print(data.head())"
```

## Implementation assumptions

- Prices use one common currency; there is no exchange-rate conversion.
- Position begins at 1, and a lower value means a better rank.
- Ratings use a 0-to-5 scale.
- Missing review counts are retained as zero.
- Rows without valid price or position are removed because core analysis requires them.
- Pipeline runs and dashboard uploads replace rather than append to SQLite.
- API extraction returns at most the first 100 shopping results per keyword by default.

## Possible improvements

- Add unit and integration tests under `tests/`.
- Add CLI options for API result limit, country, and language.
- Add structured logging, retries, and API backoff.
- Store historical runs instead of replacing the table.
- Record ingestion time and source type (`csv` or `api`).
- Use a configurable brand dictionary or entity-extraction model.
- Add currency detection and conversion.
- Make price categories configurable by market.
- Support PostgreSQL or MySQL for production.
- Add authentication and caching before public deployment.
- Add continuous integration and deployment workflows.

## Summary

The project separates responsibilities clearly:

- `data/` loads, extracts, cleans, and stores records;
- `analytics/` defines repeatable business measures;
- `dashboard/` queries and displays prepared information;
- `pipeline.py` coordinates the complete workflow;
- `app.py` launches Streamlit.

This structure makes the project easier to understand, test, extend, and present as a complete data analytics portfolio project.
