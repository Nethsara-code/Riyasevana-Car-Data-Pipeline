import csv
import sqlite3
import re
import os
import requests 
from bs4 import BeautifulSoup
from datetime import datetime

# CONFIG
BASE_URL = "https://riyasewana.com/search/cars"
MAX_PAGES = 10
DELAY_SEC = 2.5
OUTPUT_CSV = "riyasewana_cars.csv"

# Browser Setup - Methods (Sections)
SECTION = requests.Session()
SECTION.headers.update({
    "User_Agent": "Mozilla/5.0 ... Chrome/123 ...",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html ...",
    "Referer": "https://riyasewana.com/",

})


# All Links Collect
#   next page link


# Car Scrape
#   Title / Price / Year / Mileage / Make / Model
#   Gear / Fuel Type / Engine (cc) / Condition / Ad Date


# CSV file save



# MAIN