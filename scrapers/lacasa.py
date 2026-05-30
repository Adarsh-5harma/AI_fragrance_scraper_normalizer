# scrapers/lacasa.py
# Scrapes lacasadelperfume.cl (WooCommerce + Woodmart theme)
# Gender comes from the category URL — no guessing needed
# HOW TO RUN: python scrapers/lacasa.py
# OUTPUT: data/lacasa_raw.csv

import sys
import os
import requests
import csv
import time
import re
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cleaners import build_product_row

SOURCE_SITE = "lacasadelperfume.cl"
BASE_URL    = "https://lacasadelperfume.cl"
OUTPUT_FILE = "data/lacasa_raw.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
}

# ── Categories to scrape ─────────────────────────────────────

CATEGORIES = [
    {"url": f"{BASE_URL}/hombre/",          "gender": "Hombre"},
    {"url": f"{BASE_URL}/mujer/",           "gender": "Mujer"},
    {"url": f"{BASE_URL}/tienda/",          "gender": "Unknown"},
    {"url": f"{BASE_URL}/tester/",          "gender": "Unknown"},
    {"url": f"{BASE_URL}/niche-perfumes/",  "gender": "Unknown"},
]

FIELDNAMES = [
    "sku", "brand", "product_name", "variant",
    "perfume_type", "gender", "ml", "barcode",
    "sale_price", "original_price", "available",
    "source_site", "source_url", "scraped_at"
]


def fetch_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return None
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error: {e}")
        return None


def extract_products_from_page(soup, gender):
    rows = []
    cards = soup.find_all("div", class_=re.compile(r"product-grid-item"))

    for card in cards:
        # ── Product title ────────────────────────────────────
        title_tag = card.find("h3", class_="product-title")
        if not title_tag:
            continue
        link_tag   = title_tag.find("a")
        raw_title  = link_tag.get_text(strip=True) if link_tag else title_tag.get_text(strip=True)
        source_url = link_tag["href"] if link_tag and link_tag.get("href") else ""

        if not raw_title:
            continue

        # ── Brand ────────────────────────────────────────────
        brand_div = card.find("div", class_="woodmart-product-cats")
        brand = "Unknown"
        if brand_div:
            brand_link = brand_div.find("a")
            if brand_link:
                brand = brand_link.get_text(strip=True)

        # ── Availability ─────────────────────────────────────
        available = "instock" in card.get("class", [])

        # ── Prices ───────────────────────────────────────────
        sale_price     = None
        original_price = None

        price_span = card.find("span", class_="price")
        if price_span:
            # Original price — in <del> tag
            del_tag = price_span.find("del")
            if del_tag:
                original_price = del_tag.get_text(strip=True)

            # Sale price — in <ins> tag (or just the price if no discount)
            ins_tag = price_span.find("ins")
            if ins_tag:
                sale_price = ins_tag.get_text(strip=True)
            elif not del_tag:
                # No discount — just one price
                sale_price = price_span.get_text(strip=True)

        # ── Build clean row ──────────────────────────────────
        row = build_product_row(
            brand          = brand,
            product_name   = raw_title,
            gender         = gender,   # ← from category URL, reliable
            sale_price     = sale_price,
            original_price = original_price,
            available      = available,
            source_site    = SOURCE_SITE,
            source_url     = source_url,
        )
        rows.append(row)

    return rows


def get_next_page_url(soup, current_url):
    """Find the URL of the next page if it exists."""
    nav = soup.find("a", class_=re.compile(r"next"))
    if nav and nav.get("href"):
        return nav["href"]
    return None


def scrape_category(category_url, gender):
    """Scrape all pages of one category."""
    all_rows = []
    url      = category_url
    page     = 1

    while url:
        print(f"  Page {page}... ", end="", flush=True)
        soup = fetch_page(url)

        if not soup:
            print("failed.")
            break

        rows = extract_products_from_page(soup, gender)
        if not rows:
            print("0 products — done.")
            break

        all_rows.extend(rows)
        print(f"{len(rows)} products")

        # Check for next page
        url = get_next_page_url(soup, url)
        page += 1
        time.sleep(1)

    return all_rows


def scrape_lacasa():
    all_rows  = []
    seen_urls = set()

    print("[lacasa] Starting scrape...")

    for i, cat in enumerate(CATEGORIES, 1):
        print(f"\n[lacasa] [{i}/{len(CATEGORIES)}] {cat['url']} (gender={cat['gender']})")
        rows = scrape_category(cat["url"], cat["gender"])

        # Deduplicate by source URL across categories
        for row in rows:
            if row["source_url"] not in seen_urls:
                seen_urls.add(row["source_url"])
                all_rows.append(row)

    return all_rows


def save_to_csv(rows, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[lacasa] Saved {len(rows)} rows → {filepath}")


if __name__ == "__main__":
    rows = scrape_lacasa()

    if rows:
        save_to_csv(rows, OUTPUT_FILE)
        print(f"\n[lacasa] Sample — first 3:\n" + "─"*55)
        for row in rows[:3]:
            print(f"  SKU:    {row['sku']}")
            print(f"  Brand:  {row['brand']}")
            print(f"  Name:   {row['product_name']}")
            print(f"  Type:   {row['perfume_type']} | ML: {row['ml']} | Gender: {row['gender']}")
            print(f"  Price:  {row['sale_price']} (was {row['original_price']})")
            print("─"*55)
        print(f"\n[lacasa] Total: {len(rows)} products")
    else:
        print("[lacasa] No products scraped.")