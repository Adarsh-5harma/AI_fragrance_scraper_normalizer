# normalize.py
# ─────────────────────────────────────────────────────────────
# WHAT THIS DOES:
#   Queries the database for all products with Unknown gender
#   or Unknown perfume_type, sends them to Claude AI in batches,
#   and updates the database with the correct values.
#
# HOW TO RUN:
#   1. Set your API key in PowerShell:
#      $env:ANTHROPIC_API_KEY = "sk-ant-...your key..."
#
#   2. Run this script:
#      python normalize.py
#
# COST: ~$0.05-0.10 for the full database (one-time run)
# ─────────────────────────────────────────────────────────────

import os
import sys
import time

# ── Django setup ─────────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from catalog.models import Product
from utils.ai_normalizer import normalize_batch

# ── Config ───────────────────────────────────────────────────
BATCH_SIZE   = 30    # products per API call (keep under 50 for reliability)
DELAY_SEC    = 0.5   # seconds between batches (avoids rate limiting)
DRY_RUN      = False # set True to preview without saving to DB


def run_normalization():
    print("=" * 60)
    print("AI NORMALIZATION — FIXING UNKNOWN FIELDS")
    print("=" * 60)

    # ── Find products that need fixing ───────────────────────
    # A product needs fixing if gender OR perfume_type is Unknown
    products_to_fix = Product.objects.filter(
        gender="Unknown"
    ) | Product.objects.filter(
        perfume_type="Unknown"
    )

    # Deduplicate (union can create duplicates)
    products_to_fix = products_to_fix.distinct()

    total = products_to_fix.count()
    print(f"\n  Products with Unknown fields: {total}")
    print(f"  Batch size: {BATCH_SIZE} products per API call")
    print(f"  Estimated API calls: {(total // BATCH_SIZE) + 1}")
    estimated_cost = total * 80 / 1_000_000 * 0.25 + total * 40 / 1_000_000 * 1.25
    print(f"  Estimated cost: ~${estimated_cost:.3f}")

    if total == 0:
        print("\n✓ Nothing to fix — all products already normalized!")
        return

    if DRY_RUN:
        print("\n  [DRY RUN] No changes will be saved to the database.")

    print("\n  Starting normalization...\n")

    # ── Process in batches ───────────────────────────────────
    updated_gender = 0
    updated_type   = 0
    unchanged      = 0
    errors         = 0

    products_list = list(products_to_fix.values("id", "product_name", "gender", "perfume_type"))

    for i in range(0, len(products_list), BATCH_SIZE):
        batch = products_list[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(products_list) // BATCH_SIZE) + 1

        print(f"  Batch {batch_num}/{total_batches} — {len(batch)} products...", end=" ", flush=True)

        # Extract just the product names for the API call
        names = [p["product_name"] for p in batch]

        # Call Claude AI
        try:
            ai_results = normalize_batch(names)
        except Exception as e:
            print(f"FAILED: {e}")
            errors += len(batch)
            continue

        # Apply the AI results back to the database
        for product_data, ai_result in zip(batch, ai_results):
            product_id   = product_data["id"]
            old_gender   = product_data["gender"]
            old_type     = product_data["perfume_type"]
            new_gender   = ai_result.get("gender", "Unknown")
            new_type     = ai_result.get("perfume_type", "Unknown")

            # Only update fields that were Unknown and are now known
            updates = {}
            if old_gender == "Unknown" and new_gender != "Unknown":
                updates["gender"] = new_gender
                updated_gender += 1
            if old_type == "Unknown" and new_type != "Unknown":
                updates["perfume_type"] = new_type
                updated_type += 1

            if not updates:
                unchanged += 1
                continue

            if not DRY_RUN:
                try:
                    Product.objects.filter(id=product_id).update(**updates)
                except Exception as e:
                    print(f"\n    ✗ DB error for ID {product_id}: {e}")
                    errors += 1

        print(f"done.")

        # Polite delay between batches
        if i + BATCH_SIZE < len(products_list):
            time.sleep(DELAY_SEC)

    # ── Final summary ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("NORMALIZATION COMPLETE")
    print("=" * 60)
    print(f"  Gender fields fixed:       {updated_gender}")
    print(f"  Perfume type fields fixed: {updated_type}")
    print(f"  Still Unknown (ambiguous): {unchanged}")
    print(f"  Errors:                    {errors}")
    print(f"  Total processed:           {total}")

    if not DRY_RUN:
        # Final count in DB
        still_unknown_gender = Product.objects.filter(gender="Unknown").count()
        still_unknown_type   = Product.objects.filter(perfume_type="Unknown").count()
        print(f"\n  Remaining Unknown gender:       {still_unknown_gender}")
        print(f"  Remaining Unknown perfume_type: {still_unknown_type}")
        print(f"\n  View results: http://127.0.0.1:8000/admin/catalog/product/")
    else:
        print("\n  [DRY RUN] Set DRY_RUN = False to save changes.")


if __name__ == "__main__":
    # Quick check: is the API key set?
    if not os.environ.get("GEMINI_API_KEY"):
        print("\n" + "=" * 60)
        print("ERROR: GEMINI_API_KEY not set")
        print("=" * 60)
        print("\nRun this first in PowerShell:\n")
        print('  $env:GEMINI_API_KEY = "AIza...your key here..."')
        print("\nGet your FREE key at: https://aistudio.google.com/apikey")
        print("(Sign in with Google → Get API Key → Create API key)\n")
        sys.exit(1)

    run_normalization()
