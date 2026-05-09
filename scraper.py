import csv
import sqlite3
import re
import os
from datetime import datetime


# CONFIG


CSV_FILE = "riyasewana_cars.csv"
DB_FILE = "database.db"
TABLE_NAME = "cars_cleaned"
LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")


# LOGGER


def log(msg):
    print(msg)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# CLEANING FUNCTIONS


def clean_price(val):
    """
    'Rs. 10,790,000' → 10790000 (int)
    """
    if not val:
        return None
    val = re.sub(r"[^\d]", "", val)  
    return int(val) if val else None

def clean_mileage(val):
    """
    '127,618 km' → 127618 (int)
    """
    if not val:
        return None
    val = re.sub(r"[^\d]", "", val)
    return int(val) if val else None

def clean_year(val):
    """
    '2012' → 2012 (int), validate range
    """
    if not val:
        return None
    val = re.sub(r"[^\d]", "", val)
    year = int(val) if val else None
    if year and 1980 <= year <= datetime.now().year + 1:
        return year
    return None

def clean_engine(val):
    """
    '800' or '800cc' → 800 (int)
    """
    if not val:
        return None
    val = re.sub(r"[^\d]", "", val)
    return int(val) if val else None

def clean_text(val):
    """
    Strip whitespace, title case
    """
    if not val:
        return None
    return val.strip().title()

def clean_gear(val):
    """
    Normalize: 'Manual'/'Auto'/'Automatic' → standard
    """
    if not val:
        return None
    val = val.strip().lower()
    if "auto" in val:
        return "Automatic"
    elif "manual" in val or "man" in val:
        return "Manual"
    return val.title()

def clean_fuel(val):
    """
    Normalize fuel type
    """
    if not val:
        return None
    val = val.strip().lower()
    mapping = {
        "petrol": "Petrol",
        "diesel": "Diesel",
        "electric": "Electric",
        "hybrid": "Hybrid",
        "plug-in hybrid": "Hybrid",
        "cng": "CNG",
        "lng": "LNG",
    }
    for key, clean in mapping.items():
        if key in val:
            return clean
    return val.title()

def clean_condition(val):
    if not val:
        return None
    val = val.strip().lower()
    if "used" in val:
        return "Used"
    elif "recondition" in val or "recon" in val:
        return "Recondition"
    elif "unregistered" in val:
        return "Unregistered"
    elif "brand new" in val or "new" in val:
        return "Brand New"
    return val.title()

# LOAD CSV


log("=" * 50)
log(f"Pipeline started: {datetime.now()}")
log("=" * 50)

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    raw_rows = list(reader)

log(f"\n[1] Loaded CSV: {len(raw_rows)} rows")


# CLEAN EACH ROW

cleaned_rows = []
skipped = 0

for i, row in enumerate(raw_rows):
    try:
        cleaned = {
            "url":          row.get("url", "").strip(),
            "title":        clean_text(row.get("Title", "")),
            "price":        clean_price(row.get("Price", "")),
            "make":         clean_text(row.get("MAKE", "")),
            "model":        clean_text(row.get("MODEL", "")),
            "year":         clean_year(row.get("YEAR", "")),
            "mileage_km":   clean_mileage(row.get("MILEAGE", "")),
            "gear":         clean_gear(row.get("GEAR", "")),
            "fuel_type":    clean_fuel(row.get("FUEL TYPE", "")),
            "engine_cc":    clean_engine(row.get("ENGINE (CC)", "")),
            "condition":    clean_condition(row.get("CONDITION", "")),
            "location":     clean_text(row.get("LOCATION", "")),
            "ad_date":      row.get("AD DATE", "").strip(),
            "scraped_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Non Price skip 
        if cleaned["price"] is None:
            log(f"  [SKIP] Row {i+1} — no price: {cleaned['title']}")
            skipped += 1
            continue

        cleaned_rows.append(cleaned)

    except Exception as e:
        log(f"  [ERROR] Row {i+1}: {e}")
        skipped += 1

log(f"\n[2] Cleaning done:")
log(f"     Clean rows : {len(cleaned_rows)}")
log(f"     Skipped    : {skipped}")


# STATS LOG


log(f"\n[3] Data summary:")
prices  = [r["price"] for r in cleaned_rows if r["price"]]
years   = [r["year"] for r in cleaned_rows if r["year"]]
mileage = [r["mileage_km"] for r in cleaned_rows if r["mileage_km"]]

if prices:
    log(f"    Price   → min: Rs.{min(prices):,}  max: Rs.{max(prices):,}  avg: Rs.{int(sum(prices)/len(prices)):,}")
if years:
    log(f"    Year    → min: {min(years)}  max: {max(years)}")
if mileage:
    log(f"    Mileage → min: {min(mileage):,} km  max: {max(mileage):,} km  avg: {int(sum(mileage)/len(mileage)):,} km")

makes = {}
for r in cleaned_rows:
    m = r["make"] or "Unknown"
    makes[m] = makes.get(m, 0) + 1
log(f"    Makes   → {dict(sorted(makes.items(), key=lambda x: -x[1])[:5])}")


# SAVE TO DB

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
cursor.execute(f"""
    CREATE TABLE {TABLE_NAME} (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        url         TEXT,
        title       TEXT,
        price       INTEGER,
        make        TEXT,
        model       TEXT,
        year        INTEGER,
        mileage_km  INTEGER,
        gear        TEXT,
        fuel_type   TEXT,
        engine_cc   INTEGER,
        condition   TEXT,
        location    TEXT,
        ad_date     TEXT,
        scraped_at  TEXT
    )
""")

for row in cleaned_rows:
    cursor.execute(f"""
        INSERT INTO {TABLE_NAME}
        (url, title, price, make, model, year, mileage_km, gear, fuel_type, engine_cc, condition, location, ad_date, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["url"], row["title"], row["price"], row["make"], row["model"],
        row["year"], row["mileage_km"], row["gear"], row["fuel_type"],
        row["engine_cc"], row["condition"], row["location"], row["ad_date"], row["scraped_at"]
    ))

conn.commit()

# Verify
cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
count = cursor.fetchone()[0]
conn.close()

log(f"\n[4] Saved to DB: {count} records → table '{TABLE_NAME}'")
log(f"\n Pipeline complete! Log saved to: {log_path}")