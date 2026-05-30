# load_catalog.py
# ─────────────────────────────────────────────────────────────
# WHAT THIS DOES:
#   Reads master_catalog.csv and loads every row
#   into the PostgreSQL database via Django's ORM.
#
# HOW TO RUN:
#   python load_catalog.py
# ─────────────────────────────────────────────────────────────

import os
import sys
import csv
from datetime import date

# ── Tell Django which settings to use ────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

# ── Now we can import Django models ──────────────────────────
from catalog.models import Product

CSV_FILE = "data/master_catalog.csv"


def parse_int(value):
    """Convert string to int, return None if empty or invalid."""
    try:
        return int(value) if value and value.strip() else None
    except (ValueError, TypeError):
        return None


def parse_bool(value):
    """Convert 'True'/'False' string to boolean."""
    return str(value).strip().lower() == 'true'


def parse_date(value):
    """Convert date string to date object."""
    try:
        return date.fromisoformat(value.strip()) if value else date.today()
    except ValueError:
        return date.today()


def load_catalog():
    print("=" * 60)
    print("LOADING MASTER CATALOG INTO DATABASE")
    print("=" * 60)

    if not os.path.exists(CSV_FILE):
        print(f"✗ File not found: {CSV_FILE}")
        print("  Run python run_all.py first.")
        return

    created = 0
    updated = 0
    skipped = 0
    errors  = 0

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # update_or_create:
                # → if product with this sku+source_site exists → update it
                # → if it doesn't exist → create it
                # This means you can run this script multiple times safely
                obj, was_created = Product.objects.update_or_create(
                    sku         = row["sku"],
                    source_site = row["source_site"],
                    defaults    = {
                        "brand":          row["brand"],
                        "product_name":   row["product_name"],
                        "variant":        row["variant"] or None,
                        "perfume_type":   row["perfume_type"],
                        "gender":         row["gender"],
                        "ml":             parse_int(row["ml"]),
                        "barcode":        row["barcode"] or None,
                        "sale_price":     parse_int(row["sale_price"]),
                        "original_price": parse_int(row["original_price"]),
                        "available":      parse_bool(row["available"]),
                        "source_url":     row["source_url"],
                        "scraped_at":     parse_date(row["scraped_at"]),
                    }
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                errors += 1
                print(f"  ✗ Error on row {row.get('sku', '?')}: {e}")

    total = created + updated
    print(f"\n✓ Done.")
    print(f"  Created: {created} new products")
    print(f"  Updated: {updated} existing products")
    print(f"  Errors:  {errors}")
    print(f"  Total in database: {Product.objects.count()}")
    print(f"\n  Open http://127.0.0.1:8000/admin/catalog/product/")
    print(f"  to see all {total} products.")


if __name__ == "__main__":
    load_catalog()