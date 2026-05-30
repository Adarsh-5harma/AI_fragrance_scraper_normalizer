# run_all.py
import csv
import os
from datetime import datetime

from scrapers.multimarcas import scrape_multimarcas
from scrapers.lodoro import scrape_lodoro
from scrapers.elite import scrape_elite
from scrapers.lacasa import scrape_lacasa

OUTPUT_FILE = "data/master_catalog.csv"

FIELDNAMES = [
    "sku", "brand", "product_name", "variant",
    "perfume_type", "gender", "ml", "barcode",
    "sale_price", "original_price", "available",
    "source_site", "source_url", "scraped_at"
]


def run_all_scrapers():
    all_rows = []
    start    = datetime.now()

    print("=" * 60)
    print("FRAGRANCE CATALOG — MASTER SCRAPE")
    print(f"Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    print("\n[1/4] Scraping multimarcasmayorista.cl...")
    try:
        rows = scrape_multimarcas()
        all_rows.extend(rows)
        print(f"      ✓ {len(rows)} products")
    except Exception as e:
        print(f"      ✗ Failed: {e}")

    print("\n[2/4] Scraping lodoro.cl...")
    try:
        rows = scrape_lodoro()
        all_rows.extend(rows)
        print(f"      ✓ {len(rows)} products")
    except Exception as e:
        print(f"      ✗ Failed: {e}")

    print("\n[3/4] Scraping eliteperfumes-distribuidor.cl...")
    try:
        rows = scrape_elite()
        all_rows.extend(rows)
        print(f"      ✓ {len(rows)} products")
    except Exception as e:
        print(f"      ✗ Failed: {e}")
    
    print("\n[4/4] Scraping lacasadelperfume.cl...")
    try:
        rows = scrape_lacasa()
        all_rows.extend(rows)
        print(f"      ✓ {len(rows)} products")
    except Exception as e:
        print(f"      ✗ Failed: {e}")

    return all_rows, start


def save_master_catalog(rows):
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Master catalog saved → {OUTPUT_FILE}")
    print(f"  Total products: {len(rows)}")
    brands = set(r["brand"] for r in rows)
    print(f"  Unique brands:  {len(brands)}")
    sources = {}
    for r in rows:
        sources[r["source_site"]] = sources.get(r["source_site"], 0) + 1
    print(f"  By source:")
    for site, count in sources.items():
        print(f"    {site}: {count} products")


def print_sample(rows):
    print(f"\n── Sample (first 3) ───────────────────────────────")
    for row in rows[:3]:
        print(f"  Brand: {row['brand']}")
        print(f"  Name:  {row['product_name']}")
        print(f"  Price: {row['sale_price']} | From: {row['source_site']}")
        print()


if __name__ == "__main__":
    rows, start = run_all_scrapers()
    if rows:
        save_master_catalog(rows)
        print_sample(rows)
        end = datetime.now()
        print(f"✓ Done in {(end-start).seconds}s")
        print("  Now run: python load_catalog.py")
    else:
        print("\n✗ No products scraped.")