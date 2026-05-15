import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

# ═══════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════

BASE_URL   = "https://riyasewana.com/search/cars"
MAX_PAGES  = 419         
DELAY_SEC  = 2.5         
OUTPUT_CSV = "riyasewana_cars.csv"

# ═══════════════════════════════════════════════════════
# Browser Setup
# ═══════════════════════════════════════════════════════

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
    """Page HTML  BeautifulSoup object return """
    url = BASE_URL if page_number == 1 else f"{BASE_URL}/{page_number}"
    try:
        response = SESSION.get(url, timeout=15)
        response.raise_for_status()
        print(f"  ✔ Page {page_number} OK → {url}")
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"  ✘ Page {page_number} failed: {e}")
        return None


# ═══════════════════════════════════════════════════════
# All Links Collect
#   next page link
# ═══════════════════════════════════════════════════════

def get_all_car_links():
    """
    

    HTML structure (inspect confirm):
      <ul class="v-list">
        <li class="v-card promoted">
          <div class="v-card-body">
            <div class="v-card-title">
              <a href="https://riyasewana.com/buy/...">Car Title</a>
            </div>
          </div>
        </li>
      </ul>
    """

    all_links = []  

    for page_num in range(1, MAX_PAGES + 1):
        print(f"\n[Page {page_num}/{MAX_PAGES}] Links collecting...")

        # ── Step 1: Page HTML  ──────────────────────────────────
        soup = get_page(page_num)
        if soup is None:
            print("  ✘ Page load failed, skip.")
            continue

        # ── Step 2:  car cards  ───────────────────────────
        # <li class="v-card"> or <li class="v-card promoted">
        # li[class*="v-card"] = class  "v-card" word li
        cards = soup.select("li[class*='v-card']")

        if not cards:
            # Cards  = last page 
            print(f"  No Cards  — last page reached at page {page_num}.")
            break

        # ── Step 3: every card card link  ─────────────────────
        page_links_found = 0
        for card in cards:

            # <div class="v-card-title"> into <a> tag 
            link_tag = card.select_one("div.v-card-title a")

            if link_tag and link_tag.get("href"):
                url = link_tag["href"]  # href attribute = actual link

                # relative link  full URL
                if not url.startswith("http"):
                    url = "https://riyasewana.com" + url

                all_links.append(url)
                page_links_found += 1

        print(f"  → Page {page_num}: {page_links_found} links | Total: {len(all_links)}")

        # ── Step 4: next page ─────────────────────────────────────────
        # polite delay — server block 
        time.sleep(DELAY_SEC)

    print(f"\n Total links collected: {len(all_links)}")
    return all_links


# ═══════════════════════════════════════════════════════
# Car Scrape
#   Title / Price / Year / Mileage / Make / Model
#   Gear / Fuel Type / Engine (cc) / Condition / Ad Date
# ═══════════════════════════════════════════════════════

def clean(text):
    """Extra spaces, newlines remove """
    return re.sub(r"\s+", " ", text).strip() if text else None


def get_field(soup, label):
    """
    Detail page table  'Label : Value'  value 
    """
    for li in soup.select("ul.more-dtl li, .moretbl td"):
        text = clean(li.get_text())
        if text and label.lower() in text.lower():
            parts = re.split(r":\s*", text, maxsplit=1)
            if len(parts) == 2:
                return clean(parts[1])
    return None


def scrape_car(url):
    """Car detail page fields extract  dict return ."""
    try:
        response = SESSION.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ✘ Failed: {url} — {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # ── Title ───────────────────────────────────────────────────────────
    title_el = soup.select_one("h1") or soup.select_one(".page-title")
    title    = clean(title_el.get_text()) if title_el else None

    # ── Price ───────────────────────────────────────────────────────────
    price_el = soup.select_one(".price") or soup.select_one(".v-card-price")
    price    = clean(price_el.get_text()) if price_el else None

    # ── Year ────────────────────────────────────────────────────────────
    year      = get_field(soup, "Year") or get_field(soup, "Registered")

    # ── Mileage ─────────────────────────────────────────────────────────
    mileage   = get_field(soup, "Mileage")

    # ── Make ────────────────────────────────────────────────────────────
    make      = get_field(soup, "Make") or get_field(soup, "Brand")

    # ── Model ───────────────────────────────────────────────────────────
    model     = get_field(soup, "Model")

    # ── Gear ────────────────────────────────────────────────────────────
    gear      = get_field(soup, "Gear") or get_field(soup, "Transmission")

    # ── Fuel Type ───────────────────────────────────────────────────────
    fuel_type = get_field(soup, "Fuel")

    # ── Engine (cc) ─────────────────────────────────────────────────────
    engine    = get_field(soup, "Engine") or get_field(soup, "CC")

    # ── Condition ───────────────────────────────────────────────────────
    condition = get_field(soup, "Condition")

    # ── Ad Date ─────────────────────────────────────────────────────────
    date_el   = soup.select_one(".v-card-date") or soup.select_one(".ad-date")
    ad_date   = clean(date_el.get_text()) if date_el else get_field(soup, "Date")

    return {
        "Title"      : title,
        "Price"      : price,
        "Year"       : year,
        "Mileage"    : mileage,
        "Make"       : make,
        "Model"      : model,
        "Gear"       : gear,
        "Fuel Type"  : fuel_type,
        "Engine (cc)": engine,
        "Condition"  : condition,
        "Ad Date"    : ad_date,
        "URL"        : url,
    }


# ═══════════════════════════════════════════════════════
# CSV file save
# ═══════════════════════════════════════════════════════

def save_csv(data, filename):
    """List of dicts → CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8-sig")  
    print(f"\n Saved {len(df)} records → '{filename}'")
    print(df.head(3).to_string())


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  Riyasewana Car Scraper")
    print("=" * 55)

    # 1.  ad links collect 
    car_links = get_all_car_links()

    if not car_links:
        print("Links  — selectors inspect .")
        exit()

    # 2. link  data scrape 
    all_cars = []
    total = len(car_links)

    for i, link in enumerate(car_links, start=1):
        print(f"[{i}/{total}] {link}")
        car = scrape_car(link)
        if car:
            all_cars.append(car)
        time.sleep(DELAY_SEC)

    # 3. CSV save 
    if all_cars:
        save_csv(all_cars, OUTPUT_CSV)
    else:
        print(" No Data — selectors DevTools  confirm .")