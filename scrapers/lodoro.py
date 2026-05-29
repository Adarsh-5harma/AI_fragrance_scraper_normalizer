# scrapers/lodoro.py
# Scrapes lodoro.cl using Shopify's built-in JSON API
# HOW TO RUN: python scrapers/lodoro.py
# OUTPUT: data/lodoro_raw.csv

import sys
import os
import requests
import csv
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cleaners import build_product_row

SOURCE_SITE = "lodoro.cl"
BASE_URL    = "https://www.lodoro.cl/collections/perfumes/products.json"
OUTPUT_FILE = "data/lodoro_raw.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "es-CL,es;q=0.9",
    "Referer": "https://www.lodoro.cl/",
}

FIELDNAMES = [
    "sku", "brand", "product_name", "variant",
    "perfume_type", "gender", "ml", "barcode",
    "sale_price", "original_price", "available",
    "source_site", "source_url", "scraped_at"
]


def scrape_lodoro():
    all_rows = []
    page     = 1

    print("[lodoro] Starting scrape...")

    while True:
        url = f"{BASE_URL}?limit=250&page={page}"
        print(f"[lodoro] Fetching page {page}... ", end="", flush=True)

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
        except requests.exceptions.RequestException as e:
            print(f"ERROR: {e}")
            break

        if response.status_code != 200:
            print(f"HTTP {response.status_code} — stopping.")
            break

        try:
            data = response.json()
        except Exception:
            print(f"Not JSON. First 200 chars: {response.text[:200]}")
            break

        products = data.get("products", [])
        if not products:
            print("no more products.")
            break

        print(f"found {len(products)} products")

        for product in products:
            title      = product.get("title", "")
            brand      = product.get("vendor", "Unknown")
            tags       = product.get("tags", [])
            handle     = product.get("handle", "")
            source_url = f"https://www.lodoro.cl/products/{handle}"

            for variant in product.get("variants", []):
                # Shopify gives prices as strings: "24990.00"
                # clean_price() in cleaners.py handles this correctly
                row = build_product_row(
                    brand          = brand,
                    product_name   = title,
                    barcode        = variant.get("barcode") or None,
                    sale_price     = variant.get("price"),
                    original_price = variant.get("compare_at_price"),
                    available      = variant.get("available", False),
                    source_site    = SOURCE_SITE,
                    source_url     = source_url,
                    tags           = tags,
                )
                all_rows.append(row)

        time.sleep(1)
        page += 1

    return all_rows


def save_to_csv(rows, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[lodoro] Saved {len(rows)} rows → {filepath}")


if __name__ == "__main__":
    rows = scrape_lodoro()

    if rows:
        save_to_csv(rows, OUTPUT_FILE)
        print(f"\n[lodoro] Sample — first 3:\n" + "─"*55)
        for row in rows[:3]:
            print(f"  SKU:   {row['sku']}")
            print(f"  Brand: {row['brand']}")
            print(f"  Name:  {row['product_name']}")
            print(f"  Type:  {row['perfume_type']} | ML: {row['ml']} | Gender: {row['gender']}")
            print(f"  Price: {row['sale_price']} (was {row['original_price']})")
            print("─"*55)
        print(f"\n[lodoro] Total: {len(rows)} products")
    else:
        print("[lodoro] No products scraped.")
        print("The site may be blocking automated requests.")
        print("Try running from your home network.")