"""
╔══════════════════════════════════════════════════════════════╗
║         Riyasewana Car Data — Cleaning Pipeline             ║
║  Input  : riyasewana_cars.csv  (raw scrape output)          ║
║  Output : cars_cleaned.csv     (ML/analysis/DB ready)       ║
╚══════════════════════════════════════════════════════════════╝

Pipeline Steps
──────────────
  1. Load & Inspect
  2. Remove Duplicates
  3. Clean Price         → numeric (LKR)
  4. Clean Year          → integer
  5. Clean Mileage       → integer (km)
  6. Clean Engine (cc)   → integer
  7. Standardise Make    → consistent brand names
  8. Standardise Gear    → Auto / Manual / Tiptronic
  9. Standardise Fuel    → Petrol / Diesel / Hybrid / Electric
 10. Standardise Condition → Reconditioned / Used / Brand New
 11. Parse Ad Date       → datetime
 12. Handle Missing Values
 13. Outlier Detection   → flag suspicious rows
 14. Feature Engineering → Age, Price_per_km, etc.
 15. Save cleaned CSV + report
"""

import re
import sys
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
INPUT_CSV   = "riyasewana_cars.csv"    # ← change if needed
OUTPUT_CSV  = "cars_cleaned.csv"
REPORT_TXT  = "cleaning_report.txt"
CURRENT_YEAR = datetime.now().year


# ══════════════════════════════════════════════════════════════
# STEP 1 — LOAD & INSPECT
# ══════════════════════════════════════════════════════════════
def load_data(path: str) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 1 — Load & Inspect")
    print("="*60)

    if not Path(path).exists():
        sys.exit(f"[ERROR] File not found: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")

    print(f"  Rows     : {len(df):,}")
    print(f"  Columns  : {list(df.columns)}")
    print(f"\n  Missing values per column:")
    for col in df.columns:
        missing = df[col].isna().sum()
        pct     = missing / len(df) * 100
        print(f"    {col:<15} {missing:>5} ({pct:.1f}%)")

    return df


# ══════════════════════════════════════════════════════════════
# STEP 2 — REMOVE DUPLICATES
# ══════════════════════════════════════════════════════════════
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 2 — Remove Duplicates")
    print("="*60)

    before = len(df)

    # Exact URL duplicates
    df = df.drop_duplicates(subset=["URL"], keep="first")

    # Near-duplicates: same Title + Price + Year
    df = df.drop_duplicates(subset=["Title", "Price", "Year"], keep="first")

    after = len(df)
    print(f"  Removed : {before - after:,} duplicate rows")
    print(f"  Remaining: {after:,} rows")
    return df.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════
# STEP 3 — CLEAN PRICE
# ══════════════════════════════════════════════════════════════
def clean_price(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 3 — Clean Price  →  Price_LKR (numeric)")
    print("="*60)

    def parse_price(val):
        if pd.isna(val):
            return np.nan
        val = str(val).upper().replace(",", "").replace(" ", "")

        # Remove currency symbols / labels
        val = re.sub(r"(LKR|RS\.?|රු\.?)", "", val)

        # Handle shorthand: 4.5M, 3.2Mn, 15L (lakh)
        m = re.search(r"([\d.]+)\s*M", val)
        if m:
            return float(m.group(1)) * 1_000_000

        l = re.search(r"([\d.]+)\s*L", val)
        if l:
            return float(l.group(1)) * 100_000

        # Plain number
        num = re.sub(r"[^\d.]", "", val)
        return float(num) if num else np.nan

    df["Price_LKR"] = df["Price"].apply(parse_price)

    ok  = df["Price_LKR"].notna().sum()
    bad = df["Price_LKR"].isna().sum()
    print(f"  Parsed  : {ok:,}  |  Failed: {bad}")
    print(f"  Range   : {df['Price_LKR'].min():,.0f} – {df['Price_LKR'].max():,.0f} LKR")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 4 — CLEAN YEAR
# ══════════════════════════════════════════════════════════════
def clean_year(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 4 — Clean Year  →  Year_Int (integer)")
    print("="*60)

    def parse_year(val):
        if pd.isna(val):
            return np.nan
        m = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", str(val))
        return int(m.group(1)) if m else np.nan

    df["Year_Int"] = df["Year"].apply(parse_year)

    # Flag impossible years
    df.loc[df["Year_Int"] > CURRENT_YEAR, "Year_Int"] = np.nan
    df.loc[df["Year_Int"] < 1950,         "Year_Int"] = np.nan

    print(f"  Parsed  : {df['Year_Int'].notna().sum():,}")
    print(f"  Range   : {df['Year_Int'].min():.0f} – {df['Year_Int'].max():.0f}")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 5 — CLEAN MILEAGE
# ══════════════════════════════════════════════════════════════
def clean_mileage(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 5 — Clean Mileage  →  Mileage_km (integer)")
    print("="*60)

    def parse_mileage(val):
        if pd.isna(val):
            return np.nan
        val = str(val).upper().replace(",", "")

        # Convert miles → km if "MI" present
        if "MI" in val:
            num = re.sub(r"[^\d.]", "", val)
            return round(float(num) * 1.60934) if num else np.nan

        num = re.sub(r"[^\d.]", "", val)
        return int(float(num)) if num else np.nan

    df["Mileage_km"] = df["Mileage"].apply(parse_mileage)

    # Sanity: 0 – 700,000 km
    df.loc[df["Mileage_km"] > 700_000, "Mileage_km"] = np.nan
    df.loc[df["Mileage_km"] < 0,       "Mileage_km"] = np.nan

    print(f"  Parsed  : {df['Mileage_km'].notna().sum():,}")
    print(f"  Range   : {df['Mileage_km'].min():,.0f} – {df['Mileage_km'].max():,.0f} km")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 6 — CLEAN ENGINE CC
# ══════════════════════════════════════════════════════════════
def clean_engine(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 6 — Clean Engine  →  Engine_cc (integer)")
    print("="*60)

    def parse_engine(val):
        if pd.isna(val):
            return np.nan
        val = str(val).upper()

        # e.g. "1.5L" → convert to cc
        m = re.search(r"([\d.]+)\s*L\b", val)
        if m:
            return int(float(m.group(1)) * 1000)

        num = re.sub(r"[^\d]", "", val)
        cc  = int(num) if num else np.nan

        # Sanity: 50 cc – 10,000 cc
        if isinstance(cc, int) and not (50 <= cc <= 10_000):
            return np.nan
        return cc

    df["Engine_cc"] = df["Engine (cc)"].apply(parse_engine)

    print(f"  Parsed  : {df['Engine_cc'].notna().sum():,}")
    print(f"  Range   : {df['Engine_cc'].min():.0f} – {df['Engine_cc'].max():.0f} cc")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 7 — STANDARDISE MAKE (Brand)
# ══════════════════════════════════════════════════════════════
# Map common raw spellings → clean name
MAKE_MAP = {
    # Toyota
    "TOYOTA": "Toyota", "TOYO": "Toyota",
    # Honda
    "HONDA": "Honda",
    # Nissan
    "NISSAN": "Nissan", "DATSUN": "Nissan",
    # Suzuki
    "SUZUKI": "Suzuki", "MARUTI": "Suzuki",
    # Mitsubishi
    "MITSUBISHI": "Mitsubishi", "MITS": "Mitsubishi",
    # Hyundai
    "HYUNDAI": "Hyundai",
    # Kia
    "KIA": "Kia",
    # BMW
    "BMW": "BMW",
    # Mercedes
    "MERCEDES": "Mercedes-Benz", "MERCEDES-BENZ": "Mercedes-Benz",
    "BENZ": "Mercedes-Benz",
    # Audi
    "AUDI": "Audi",
    # Mazda
    "MAZDA": "Mazda",
    # Subaru
    "SUBARU": "Subaru",
    # Perodua
    "PERODUA": "Perodua",
    # Isuzu
    "ISUZU": "Isuzu",
    # Ford
    "FORD": "Ford",
    # Volkswagen
    "VOLKSWAGEN": "Volkswagen", "VW": "Volkswagen",
    # Jeep
    "JEEP": "Jeep",
}

def standardise_make(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 7 — Standardise Make")
    print("="*60)

    def clean_make(val):
        if pd.isna(val):
            return np.nan
        key = str(val).upper().strip()
        # Exact map lookup
        if key in MAKE_MAP:
            return MAKE_MAP[key]
        # Partial match
        for k, v in MAKE_MAP.items():
            if k in key:
                return v
        # Title-case fallback
        return str(val).strip().title()

    df["Make_Clean"] = df["Make"].apply(clean_make)

    top10 = df["Make_Clean"].value_counts().head(10)
    print("  Top 10 makes:")
    for make, cnt in top10.items():
        print(f"    {make:<20} {cnt:>5}")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 8 — STANDARDISE GEAR / TRANSMISSION
# ══════════════════════════════════════════════════════════════
def standardise_gear(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 8 — Standardise Gear")
    print("="*60)

    def clean_gear(val):
        if pd.isna(val):
            return np.nan
        val = str(val).upper()
        if any(x in val for x in ["AUTO", "AT", "AUTOMATIC"]):
            return "Automatic"
        if any(x in val for x in ["MANUAL", "MT", "STICK"]):
            return "Manual"
        if "TIP" in val or "SPORT" in val:
            return "Tiptronic"
        if "CVT" in val:
            return "CVT"
        return "Other"

    df["Gear_Clean"] = df["Gear"].apply(clean_gear)
    print(f"  Distribution:\n{df['Gear_Clean'].value_counts().to_string()}")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 9 — STANDARDISE FUEL TYPE
# ══════════════════════════════════════════════════════════════
def standardise_fuel(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 9 — Standardise Fuel Type")
    print("="*60)

    def clean_fuel(val):
        if pd.isna(val):
            return np.nan
        val = str(val).upper()
        if "HYBRID" in val:
            return "Hybrid"
        if "ELECT" in val or "EV" in val:
            return "Electric"
        if "DIESEL" in val:
            return "Diesel"
        if "PETROL" in val or "GASOLINE" in val or "GAS" in val:
            return "Petrol"
        if "CNG" in val or "LPG" in val or "GAS" in val:
            return "CNG/LPG"
        return "Other"

    df["Fuel_Clean"] = df["Fuel Type"].apply(clean_fuel)
    print(f"  Distribution:\n{df['Fuel_Clean'].value_counts().to_string()}")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 10 — STANDARDISE CONDITION
# ══════════════════════════════════════════════════════════════
def standardise_condition(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 10 — Standardise Condition")
    print("="*60)

    def clean_condition(val):
        if pd.isna(val):
            return np.nan
        val = str(val).upper()
        if "RECOND" in val or "RECON" in val:
            return "Reconditioned"
        if "BRAND" in val or "NEW" in val:
            return "Brand New"
        if "USED" in val or "REGISTERED" in val or "LOCAL" in val:
            return "Used"
        return "Other"

    df["Condition_Clean"] = df["Condition"].apply(clean_condition)
    print(f"  Distribution:\n{df['Condition_Clean'].value_counts().to_string()}")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 11 — PARSE AD DATE
# ══════════════════════════════════════════════════════════════
def parse_ad_date(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 11 — Parse Ad Date")
    print("="*60)

    # Try multiple date formats seen on Riyasewana
    DATE_FORMATS = [
        "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y",
        "%B %d, %Y", "%b %d, %Y",
        "%d %B %Y", "%d %b %Y",
    ]

    def parse_date(val):
        if pd.isna(val):
            return pd.NaT
        for fmt in DATE_FORMATS:
            try:
                return pd.to_datetime(str(val).strip(), format=fmt)
            except ValueError:
                continue
        # Last resort: pandas auto-parse
        try:
            return pd.to_datetime(val, dayfirst=True)
        except Exception:
            return pd.NaT

    df["Ad_Date"] = df["Ad Date"].apply(parse_date)
    parsed = df["Ad_Date"].notna().sum()
    print(f"  Parsed  : {parsed:,} / {len(df):,}")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 12 — HANDLE MISSING VALUES
# ══════════════════════════════════════════════════════════════
def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 12 — Handle Missing Values")
    print("="*60)

    # Drop rows with NO price at all (useless for ML/analysis)
    before = len(df)
    df = df[df["Price_LKR"].notna()].copy()
    print(f"  Dropped {before - len(df)} rows with missing Price")

    # Fill categorical nulls with 'Unknown'
    for col in ["Make_Clean", "Gear_Clean", "Fuel_Clean", "Condition_Clean"]:
        df[col] = df[col].fillna("Unknown")

    # Numeric: fill with median (safe for skewed data)
    for col in ["Mileage_km", "Engine_cc"]:
        med = df[col].median()
        df[col] = df[col].fillna(med)
        print(f"  {col} median fill: {med:,.0f}")

    print(f"  Remaining rows: {len(df):,}")
    return df.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════
# STEP 13 — OUTLIER DETECTION (IQR method)
# ══════════════════════════════════════════════════════════════
def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 13 — Outlier Detection (IQR)")
    print("="*60)

    df["Is_Outlier"] = False

    for col in ["Price_LKR", "Mileage_km", "Engine_cc"]:
        if col not in df.columns:
            continue
        Q1  = df[col].quantile(0.25)
        Q3  = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 3 * IQR
        upper = Q3 + 3 * IQR

        mask = (df[col] < lower) | (df[col] > upper)
        df.loc[mask, "Is_Outlier"] = True
        print(f"  {col:<15}  bounds [{lower:,.0f} – {upper:,.0f}]"
              f"   flagged: {mask.sum()}")

    total_outliers = df["Is_Outlier"].sum()
    print(f"\n  Total flagged rows: {total_outliers} "
          f"({total_outliers/len(df)*100:.1f}%)")
    print("  Note: Outliers are FLAGGED, not removed — you decide!")
    return df


# ══════════════════════════════════════════════════════════════
# STEP 14 — FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════
def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("  STEP 14 — Feature Engineering")
    print("="*60)

    # Car Age
    df["Car_Age"] = CURRENT_YEAR - df["Year_Int"]
    df.loc[df["Car_Age"] < 0, "Car_Age"] = np.nan
    print("  ✔ Car_Age = CurrentYear - Year_Int")

    # Price per km (value metric)
    df["Price_per_km"] = (df["Price_LKR"] / df["Mileage_km"]).replace([np.inf, -np.inf], np.nan)
    print("  ✔ Price_per_km = Price_LKR / Mileage_km")

    # Log Price (normalised for ML)
    df["Log_Price"] = np.log1p(df["Price_LKR"])
    print("  ✔ Log_Price = log(1 + Price_LKR)")

    # Price band (for segmentation)
    bins   = [0, 1e6, 3e6, 6e6, 10e6, 20e6, np.inf]
    labels = ["< 1M", "1–3M", "3–6M", "6–10M", "10–20M", "20M+"]
    df["Price_Band"] = pd.cut(df["Price_LKR"], bins=bins, labels=labels)
    print("  ✔ Price_Band created (6 bands)")

    # Is Premium Brand
    premium = {"BMW", "Mercedes-Benz", "Audi", "Porsche", "Lexus", "Volvo"}
    df["Is_Premium"] = df["Make_Clean"].isin(premium).astype(int)
    print("  ✔ Is_Premium flag")

    return df


# ══════════════════════════════════════════════════════════════
# STEP 15 — SAVE OUTPUT + REPORT
# ══════════════════════════════════════════════════════════════
def save_output(df: pd.DataFrame):
    print("\n" + "="*60)
    print("  STEP 15 — Save Cleaned Data & Report")
    print("="*60)

    # ── Final column selection ────────────────────────────────
    clean_cols = [
        # Originals (raw — kept for reference)
        "Title", "URL",
        # Cleaned numerics
        "Price_LKR", "Year_Int", "Mileage_km", "Engine_cc",
        # Cleaned categoricals
        "Make_Clean", "Model",
        "Gear_Clean", "Fuel_Clean", "Condition_Clean",
        # Dates
        "Ad_Date",
        # Engineered features
        "Car_Age", "Price_per_km", "Log_Price",
        "Price_Band", "Is_Premium",
        # QA
        "Is_Outlier",
    ]

    # Keep only columns that exist
    clean_cols = [c for c in clean_cols if c in df.columns]
    df_out = df[clean_cols].copy()
    df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"  ✔ Saved  : {OUTPUT_CSV}  ({len(df_out):,} rows × {len(clean_cols)} cols)")

    # ── Text Report ───────────────────────────────────────────
    report_lines = [
        "=" * 60,
        "  Riyasewana Cleaning Report",
        f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        f"  Total clean rows  : {len(df_out):,}",
        f"  Outlier rows      : {df_out['Is_Outlier'].sum():,}",
        "",
        "  Price Summary (LKR)",
        f"    Min    : {df_out['Price_LKR'].min():>15,.0f}",
        f"    Median : {df_out['Price_LKR'].median():>15,.0f}",
        f"    Mean   : {df_out['Price_LKR'].mean():>15,.0f}",
        f"    Max    : {df_out['Price_LKR'].max():>15,.0f}",
        "",
        "  Year Range",
        f"    {df_out['Year_Int'].min():.0f}  –  {df_out['Year_Int'].max():.0f}",
        "",
        "  Top 5 Makes",
    ]
    for make, cnt in df_out["Make_Clean"].value_counts().head(5).items():
        report_lines.append(f"    {make:<20} {cnt:>5}")

    report_lines += [
        "",
        "  Fuel Type Distribution",
    ]
    for fuel, cnt in df_out["Fuel_Clean"].value_counts().items():
        report_lines.append(f"    {fuel:<20} {cnt:>5}")

    report_lines += [
        "",
        "  Condition Distribution",
    ]
    for cond, cnt in df_out["Condition_Clean"].value_counts().items():
        report_lines.append(f"    {cond:<20} {cnt:>5}")

    report_lines.append("=" * 60)

    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"  ✔ Report : {REPORT_TXT}")
    print("\n" + "\n".join(report_lines))


# ══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════
def run_pipeline():
    print("\n" + "█"*60)
    print("  Riyasewana Car Data — Cleaning Pipeline")
    print("█"*60)

    df = load_data(INPUT_CSV)
    df = remove_duplicates(df)
    df = clean_price(df)
    df = clean_year(df)
    df = clean_mileage(df)
    df = clean_engine(df)
    df = standardise_make(df)
    df = standardise_gear(df)
    df = standardise_fuel(df)
    df = standardise_condition(df)
    df = parse_ad_date(df)
    df = handle_missing(df)
    df = flag_outliers(df)
    df = feature_engineering(df)
    save_output(df)

    print("\n" + "█"*60)
    print("  Pipeline complete! ✔")
    print("█"*60 + "\n")


if __name__ == "__main__":
    run_pipeline()