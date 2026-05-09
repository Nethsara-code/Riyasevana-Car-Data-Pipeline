from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time
import random


# CONFIG


SEARCH_URL = "https://riyasewana.com/search/cars"   
MAX_PAGES = 5                                        
OUTPUT_FILE = "riyasewana_cars.csv"

# BROWSER SETUP


options = Options()

options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
wait = WebDriverWait(driver, 15)


#  ALL LINKS COLLECT 


def get_links_from_page():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = []
    for card in soup.select("ul.v-list li.v-card"):
        a = card.select_one("div.v-card-img a")
        if a and a.get("href") and "/buy/" in a["href"]:
            href = a["href"]
            if not href.startswith("http"):
                href = "https://riyasewana.com" + href
            links.append(href)
    return links

all_links = []

print("=== Collecting car links ===")
driver.get(SEARCH_URL)
time.sleep(3)

for page_num in range(1, MAX_PAGES + 1):
    print(f"Page {page_num}...", end=" ")

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.v-list")))
    except:
        print("List not found, stopping.")
        break

    page_links = get_links_from_page()
    new_links = [l for l in page_links if l not in all_links]
    all_links.extend(new_links)
    print(f"{len(new_links)} links found (total: {len(all_links)})")

    if not new_links:
        print("No new links, stopping.")
        break

    # Next page button
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.next, a[rel='next'], .pagination .next a")
        next_url = next_btn.get_attribute("href")
        if next_url:
            driver.get(next_url)
            time.sleep(random.uniform(2, 3))
        else:
            break
    except:
        print("No next page, done.")
        break

print(f"\nTotal links collected: {len(all_links)}")


#  CAR SCRAPE 


all_cars = []

print("\n=== Scraping car details ===")
for i, link in enumerate(all_links):
    print(f"[{i+1}/{len(all_links)}] {link}")

    try:
        driver.get(link)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "detail-card")))
        time.sleep(random.uniform(1.5, 2.5))

        data = {"url": link}

        # Title
        try:
            data["Title"] = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            data["Title"] = ""

        # Price
        try:
            data["Price"] = driver.find_element(By.CLASS_NAME, "price-amount").text.strip()
        except:
            data["Price"] = ""

        # Detail rows
        cards = driver.find_elements(By.CLASS_NAME, "detail-card")
        for card in cards:
            rows = card.find_elements(By.CLASS_NAME, "detail-row")
            for row in rows:
                try:
                    label = row.find_element(By.CLASS_NAME, "detail-label").text.strip()
                    value = row.find_element(By.CLASS_NAME, "detail-value").text.strip()
                    if label and value:
                        data[label] = value
                except:
                    pass

        all_cars.append(data)
        print(f"  ✓ {data.get('Title', '?')} | {data.get('Price', 'N/A')}")

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        all_cars.append({"url": link, "error": str(e)})

    time.sleep(random.uniform(2, 4))

driver.quit()

#  CSV FILE SAVE

if all_cars:
    all_keys = []
    for car in all_cars:
        for key in car.keys():
            if key not in all_keys:
                all_keys.append(key)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(all_cars)

    print(f"\n Saved {len(all_cars)} cars to '{OUTPUT_FILE}'")
else:
    print("\n No data scraped.")