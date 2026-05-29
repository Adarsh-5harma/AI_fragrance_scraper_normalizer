# scrapers/multimarcas.py
# ─────────────────────────────────────────────────────────────
# Scrapes multimarcasmayorista.cl (Jumpseller platform)
# Jumpseller pagination: /?page=2, /?page=3 etc.
# But we detect when we're seeing duplicate products and stop.
# ─────────────────────────────────────────────────────────────

import sys
import os
import requests
import csv
import time
import re
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cleaners import build_product_row

SOURCE_SITE = "multimarcasmayorista.cl"
BASE_URL    = "https://www.multimarcasmayorista.cl"
OUTPUT_FILE = "data/multimarcas_raw.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
}

FIELDNAMES = [
    "sku", "brand", "product_name", "variant",
    "perfume_type", "gender", "ml", "barcode",
    "sale_price", "original_price", "available",
    "source_site", "source_url", "scraped_at"
]


def fetch_page(page_number):
    if page_number == 1:
        url = f"{BASE_URL}/"
    else:
        url = f"{BASE_URL}/?page={page_number}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return [], None
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.find_all("div", class_="product-block trsn mb-3")
        return cards, soup
    except Exception as e:
        print(f"Error: {e}")
        return [], None


def extract_product(card):
    caption   = card.find("div", class_="caption")
    title_tag = caption.find("a") if caption else None
    raw_title = title_tag.get_text(strip=True) if title_tag else ""

    if not raw_title:
        return None

    # Product URL
    source_url = ""
    if title_tag and title_tag.get("href"):
        href = title_tag["href"]
        source_url = href if href.startswith("http") else BASE_URL + href

    # Brand — extract from title, fall back to URL when truncated
    brand        = "Unknown"
    product_name = raw_title
    parts        = re.split(r'\s*[-–]\s*', raw_title)

    if len(parts) >= 2 and "..." not in parts[-1]:
        # Title is clean — brand is after the dash
        brand        = parts[-1].strip()
        product_name = parts[0].strip()

    elif source_url and "/" in source_url:
        # Title is truncated — get brand from URL slug
        slug       = source_url.rstrip("/").split("/")[-1]
        slug_parts = slug.split("-") if slug else []
        stop_words = {
            "edp", "edt", "parfum", "edc", "ml", "spray",
            "100", "75", "50", "150", "200", "30", "125",
            "105", "90", "60", "35", "tester", "recargable"
        }

        brand_start = 0
        for i, part in enumerate(slug_parts):
            if part.lower() in stop_words:
                brand_start = i + 1

        if brand_start > 0 and brand_start < len(slug_parts):
            brand = " ".join(slug_parts[brand_start:]).upper()

        # Clean dots from product name
        product_name = parts[0].replace("...", "").strip() if len(parts) >= 2 else raw_title.replace("...", "").strip()

    # Prices
    price_div      = card.find("div", class_="list-price")
    sale_price     = None
    original_price = None

    if price_div:
        strong = price_div.find("strong")
        if strong:
            sale_price = strong.get_text(strip=True)
        crossed = price_div.find("s") or price_div.find("del")
        if crossed:
            original_price = crossed.get_text(strip=True)
        if not sale_price:
            found = re.findall(r'\$[\d\.]+', price_div.get_text())
            if found:
                sale_price = found[0]
            if len(found) > 1:
                original_price = found[1]

    # Availability
    out_of_stock = card.find(class_=re.compile(r'out.of.stock|agotado|sin.stock', re.I))
    available    = out_of_stock is None

    return build_product_row(
        brand          = brand,
        product_name   = product_name,
        sale_price     = sale_price,
        original_price = original_price,
        available      = available,
        source_site    = SOURCE_SITE,
        source_url     = source_url,
    )


def scrape_multimarcas():
    all_rows     = []
    seen_urls    = set()   # ← KEY: track URLs we've already seen
    page         = 1

    print(f"[multimarcas] Starting scrape...")

    while True:
        print(f"[multimarcas] Page {page}... ", end="", flush=True)

        cards, soup = fetch_page(page)

        if not cards:
            print("no products found — stopping.")
            break

        # ── Duplicate detection ──────────────────────────────
        # Extract URLs from this page
        page_urls = set()
        for card in cards:
            caption   = card.find("div", class_="caption")
            title_tag = caption.find("a") if caption else None
            if title_tag and title_tag.get("href"):
                page_urls.add(title_tag["href"])

        # If ALL URLs on this page were already seen → we've looped back
        if page_urls and page_urls.issubset(seen_urls):
            print(f"duplicate page detected — stopping.")
            break

        # Add new URLs to seen set
        seen_urls.update(page_urls)

        # ── Extract products ─────────────────────────────────
        page_rows = []
        for card in cards:
            row = extract_product(card)
            if row:
                page_rows.append(row)

        all_rows.extend(page_rows)
        print(f"{len(page_rows)} products")

        # ── Check if there's a next page ─────────────────────
        # Look for pagination links in the HTML
        next_page = None
        if soup:
            # Jumpseller pagination: look for a link with page=N+1
            next_link = soup.find("a", href=re.compile(rf'page={page+1}'))
            if next_link:
                next_page = page + 1

        if not next_page:
            print(f"[multimarcas] No page {page+1} found — done.")
            break

        time.sleep(1)
        page += 1

    return all_rows


def save_to_csv(rows, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[multimarcas] Saved {len(rows)} rows → {filepath}")


if __name__ == "__main__":
    rows = scrape_multimarcas()

    if rows:
        save_to_csv(rows, OUTPUT_FILE)

        print(f"\n[multimarcas] Sample — first 5:\n" + "─"*55)
        for row in rows[:5]:
            print(f"  SKU:   {row['sku']}")
            print(f"  Brand: {row['brand']}")
            print(f"  Name:  {row['product_name']}")
            print(f"  Type:  {row['perfume_type']} | ML: {row['ml']} | Gender: {row['gender']}")
            print(f"  Price: {row['sale_price']} (was {row['original_price']})")
            print("─"*55)

        print(f"\n[multimarcas] Total: {len(rows)} products scraped.")
    else:
        print("[multimarcas] No products found.")