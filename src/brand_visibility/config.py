from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DEFAULT_CSV = RAW_DIR / "brand_dataset.csv"
CLEAN_CSV = PROCESSED_DIR / "brand_visibility_clean.csv"
DATABASE = PROCESSED_DIR / "brand_visibility.db"
TABLE_NAME = "products"

EXPECTED_COLUMNS = [
    "keyword", "title", "price", "raw_price", "rating", "reviews",
    "platform", "position", "delivery", "link", "thumbnail",
]

BRANDS = [
    "Apple", "Samsung", "Sony", "Dell", "HP", "Lenovo", "Asus", "Acer",
    "Nike", "Adidas", "Puma", "New Balance", "LG", "Google", "Microsoft",
]
