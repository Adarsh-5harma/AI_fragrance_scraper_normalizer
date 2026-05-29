# scrapers/multimarcas.py
# Scraper for Multimarcas.cl - Chilean perfume retailer

import sys
import os
import requests
import csv
import time
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cleaners import build_product_row

# Configuration
SOURCE_SITE = 'multimarcas.cl'
BASE_URL = "https://www.multimarcas.cl/products.json"
OUTPUT_FILE = "data/multimarcas_raw.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-CL,es;q=0.9",
    "Referer": "https://www.multimarcas.cl/",
}

FIELDNAMES = [
    "sku", "brand", "product_name", "variant",
    "perfume_type", "gender", "ml", "barcode",
    "sale_price", "original_price", "available",
    "source_site", "source_url", "scraped_at"
]

def scrape_multimarcas():
    """Scrape products from Multimarcas.cl"""
    all_rows = []
    page = 1
    
    print(f"[{SOURCE_SITE}] Starting scrape...")
    
    while True:
        url = f"{BASE_URL}?limit=250&page={page}"
        print(f"[{SOURCE_SITE}] Fetching page {page}... ", end="", flush=True)
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code != 200:
                print(f"HTTP {response.status_code} - stopping.")
                break
            
            data = response.json()
            products = data.get("products", [])
            
            if not products:
                print("no more products.")
                break
            
            print(f"found {len(products)} products")
            
            for product in products:
                title = product.get("title", "")
                if not title:
                    continue
                
                brand = product.get("vendor", "Unknown")
                tags = product.get("tags", [])
                handle = product.get("handle", "")
                source_url = f"https://www.multimarcas.cl/products/{handle}"
                variants = product.get("variants", [])
                
                for variant in variants:
                    # Parse prices (Shopify format)
                    sale_price_raw = variant.get("price")
                    original_price_raw = variant.get("compare_at_price")
                    
                    # Convert to cents
                    if sale_price_raw:
                        try:
                            sale_price_cents = str(int(float(sale_price_raw) * 100))
                        except:
                            sale_price_cents = None
                    else:
                        sale_price_cents = None
                    
                    if original_price_raw:
                        try:
                            original_price_cents = str(int(float(original_price_raw) * 100))
                        except:
                            original_price_cents = None
                    else:
                        original_price_cents = None
                    
                    barcode = variant.get("barcode") or variant.get("sku") or None
                    available = variant.get("available", False)
                    variant_title = variant.get("title", "")
                    
                    row = build_product_row(
                        brand=brand,
                        product_name=title,
                        variant=variant_title if variant_title != "Default Title" else None,
                        perfume_type=None,
                        gender=None,
                        ml=None,
                        barcode=barcode,
                        sale_price=sale_price_cents,
                        original_price=original_price_cents,
                        available=available,
                        source_site=SOURCE_SITE,
                        source_url=source_url,
                        tags=tags,
                    )
                    all_rows.append(row)
            
            time.sleep(1)
            page += 1
            
            # Safety limit
            if page > 50:
                print("Reached page limit (50)")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"JSON error: {e}")
            break
    
    return all_rows

def save_to_csv(rows, filepath):
    """Save scraped data to CSV"""
    if not rows:
        print(f"[{SOURCE_SITE}] No data to save")
        return
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"[{SOURCE_SITE}] Saved {len(rows)} rows → {filepath}")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    
    print("\n" + "=" * 60)
    print("MULTIMARCAS.CL SCRAPER")
    print("=" * 60 + "\n")
    
    rows = scrape_multimarcas()
    
    if rows:
        save_to_csv(rows, OUTPUT_FILE)
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"data/multimarcas_raw_{timestamp}.csv"
        save_to_csv(rows, backup_file)
        
        # Statistics
        unique_skus = len(set(row['sku'] for row in rows))
        unique_brands = len(set(row['brand'] for row in rows))
        
        print(f"\n📊 Statistics:")
        print(f"   Total rows: {len(rows)}")
        print(f"   Unique SKUs: {unique_skus}")
        print(f"   Unique brands: {unique_brands}")
        
        # Sample
        print(f"\n📋 Sample (first product):")
        if rows:
            row = rows[0]
            print(f"   Brand: {row['brand']}")
            print(f"   Name:  {row['product_name'][:60]}")
            if row['sale_price']:
                print(f"   Price: ${row['sale_price']/100:.2f}")
        
        print("\n✅ Data ready for master database")
    else:
        print(f"[{SOURCE_SITE}] ❌ No products scraped")
        print("\nPossible issues:")
        print("1. Site might not be accessible")
        print("2. API endpoint might be different")
        print("3. Site might require different headers")