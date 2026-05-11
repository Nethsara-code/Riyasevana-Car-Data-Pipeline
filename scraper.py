import csv
import sqlite3
import re
import os
import time
import requests 
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# CONFIG
BASE_URL = "https://riyasewana.com/search/cars"
MAX_PAGES = 10
DELAY_SEC = 2.5
OUTPUT_CSV = "riyasewana_cars.csv"

# Browser Setup - Methods (Sections)
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://riyasewana.com/",
})
 
 
def get_page(page_number):
    
    url = BASE_URL if page_number == 1 else f"{BASE_URL}/{page_number}"
    try:
        response = SESSION.get(url, timeout=15)
        response.raise_for_status()
        print(f"  ✔ Page {page_number} OK → {url}")
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"  ✘ Page {page_number} failed: {e}")
        return None


# All Links Collect
def get_all_links():

    all_links = []

    for page_num in range(1, MAX_PAGES + 1):
        print(f"\n[Page {page_num}/{MAX_PAGES}] Links Collecting...")

        soup = get_page(page_num)
        if soup is None:
            print(" X page load failed")
            continue

        cards = soup.select("li[class*='v-card']")


        if not cards:
            print(f"  NO Cards  — last page reached at page {page_num}.")
            break
        
        page_links_found = 0
        for card in cards:

            link_tag = card.select_one("div.v-card-title a")

            if link_tag and link_tag.get("href"):
                url = link_tag["herf"]

                if not url.startswith("http"):
                    url = "https://riyasewana.com" + url

                all_links.append(url)
                page_links_found += 1

        print(f"Page {page_num}: {page_links_found} links | Total: {len(all_links)} ")

        time.sleep(DELAY_SEC)

        print(f"\n✅ Total links collected: {len(all_links)}")
        return all_links
        
        
#   next page link


# Car Scrape
#   Title / Price / Year / Mileage / Make / Model
#   Gear / Fuel Type / Engine (cc) / Condition / Ad Date


# CSV file save



# MAIN