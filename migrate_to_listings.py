# migrate_to_listings.py
# Migrates existing Product rows into ProductListing rows
# Run once: python migrate_to_listings.py

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from catalog.models import Product, Source, ProductListing
from datetime import date

print("Migrating products to listings...")

# Get all sources
sources = {s.name: s for s in Source.objects.all()}
print(f"Sources found: {list(sources.keys())}")

created = 0
skipped = 0

for product in Product.objects.all():
    source = sources.get(product.source_site)

    if not source:
        skipped += 1
        continue

    listing, was_created = ProductListing.objects.get_or_create(
        product = product,
        source  = source,
        defaults = {
            "source_url":     product.source_url,
            "sale_price":     product.sale_price,
            "original_price": product.original_price,
            "available":      product.available,
            "scraped_at":     product.scraped_at,
        }
    )

    if was_created:
        created += 1

print(f"\n✓ Done.")
print(f"  Listings created: {created}")
print(f"  Skipped:          {skipped}")
print(f"  Total listings:   {ProductListing.objects.count()}")