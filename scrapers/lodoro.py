# scrapers/lodoro.py - SIMPLE WORKING VERSION

import sys
import os
import requests
import csv
import time
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cleaners import build_product_row

SOURCE_SITE = 'lodoro.cl'
BASE_URL = "https://www.lodoro.cl/products.json"
OUTPUT_FILE = "data/lodoro_raw.csv"

# Simple headers that work (no session, no rotation)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

FIELDNAMES = [
    "sku", "brand", "product_name", "variant",
    "perfume_type", "gender", "ml", "barcode",
    "sale_price", "original_price", "available",
    "source_site", "source_url", "scraped_at"
]

def scrape_lodoro():
    """Simple scraper that works with lodoro.cl"""
    all_rows = []
    page = 1
    
    print(f"[lodoro] Starting scrape...")
    
    while True:
        url = f"{BASE_URL}?limit=250&page={page}"
        print(f"[lodoro] Fetching page {page}... ", end="", flush=True)
        
        try:
            # Simple GET request - no session, minimal headers
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code != 200:
                print(f"HTTP {response.status_code} - stopping.")
                break
            
            # Parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"JSON error: {e}")
                print(f"Response preview: {response.text[:200]}")
                break
            
            products = data.get("products", [])
            
            if not products:
                print("no more products.")
                break
            
            print(f"found {len(products)} products")
            
            # Process each product
            for product in products:
                title = product.get("title", "")
                if not title:
                    continue
                
                brand = product.get("vendor", "Unknown")
                tags = product.get("tags", [])
                handle = product.get("handle", "")
                source_url = f"https://www.lodoro.cl/products/{handle}"
                variants = product.get("variants", [])
                
                for variant in variants:
                    # Shopify returns prices as strings like "49.99"
                    sale_price_raw = variant.get("price")
                    original_price_raw = variant.get("compare_at_price")
                    
                    # Convert to cents (e.g., "49.99" -> "4999")
                    if sale_price_raw:
                        try:
                            sale_price_cents = str(int(float(sale_price_raw) * 100))
                        except (ValueError, TypeError):
                            sale_price_cents = None
                    else:
                        sale_price_cents = None
                    
                    if original_price_raw:
                        try:
                            original_price_cents = str(int(float(original_price_raw) * 100))
                        except (ValueError, TypeError):
                            original_price_cents = None
                    else:
                        original_price_cents = None
                    
                    barcode = variant.get("barcode") or None
                    available = variant.get("available", False)
                    variant_title = variant.get("title", "")
                    
                    # Build product row using shared cleaner
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
            
            # Polite delay between pages
            time.sleep(1)
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            break
    
    return all_rows

def save_to_csv(rows, filepath):
    """Save scraped data to CSV"""
    if not rows:
        print("[lodoro] No data to save")
        return
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"[lodoro] Saved {len(rows)} rows → {filepath}")

if __name__ == "__main__":
    # Create directories
    os.makedirs("data", exist_ok=True)
    
    print("\n" + "=" * 60)
    print("LODORO.CL SCRAPER")
    print("=" * 60 + "\n")
    
    # Run scraper
    rows = scrape_lodoro()
    
    if rows:
        # Save to CSV
        save_to_csv(rows, OUTPUT_FILE)
        
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"data/lodoro_raw_{timestamp}.csv"
        save_to_csv(rows, backup_file)
        
        # Statistics
        unique_skus = len(set(row['sku'] for row in rows))
        unique_brands = len(set(row['brand'] for row in rows))
        with_prices = sum(1 for row in rows if row['sale_price'])
        with_sizes = sum(1 for row in rows if row['ml'])
        
        print(f"\n📊 Scraping Statistics:")
        print(f"   Total rows: {len(rows)}")
        print(f"   Unique SKUs: {unique_skus}")
        print(f"   Unique brands: {unique_brands}")
        print(f"   Products with prices: {with_prices}/{len(rows)} ({with_prices/len(rows)*100:.1f}%)")
        print(f"   Products with sizes: {with_sizes}/{len(rows)} ({with_sizes/len(rows)*100:.1f}%)")
        
        # Sample output
        print(f"\n📋 Sample — first 3 products:")
        print("─" * 60)
        for i, row in enumerate(rows[:3], 1):
            print(f"\n   Product {i}:")
            print(f"   Brand:  {row['brand']}")
            print(f"   Name:   {row['product_name'][:70]}")
            print(f"   SKU:    {row['sku']}")
            if row['sale_price']:
                print(f"   Price:  ${row['sale_price']/100:,.2f}")
            if row['original_price']:
                print(f"   Orig.:  ${row['original_price']/100:,.2f}")
            print(f"   Type:   {row['perfume_type']}")
            print(f"   Gender: {row['gender']}")
            print(f"   ML:     {row['ml'] if row['ml'] else 'N/A'}")
            print("─" * 60)
        
        print("\n✅ Data ready for Phase 1 Master Database")
        
    else:
        print("[lodoro] ❌ No products scraped.")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Verify site is accessible: https://www.lodoro.cl")
        print("3. Run: python debug_lodoro.py")