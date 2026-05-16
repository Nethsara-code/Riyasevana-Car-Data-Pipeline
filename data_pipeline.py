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

import os 
import sys
import warnings
from  pathlib import path 
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# =================================================
# Config
# =================================================

INPUT_CSV = "riyasewana_cars.csv"
OUTPUT_CSV = "cars_cleaned.csv"
REPORT_FILE = "data_cleaning_report.txt"
CURRENT_YEAR = datetime.now().year