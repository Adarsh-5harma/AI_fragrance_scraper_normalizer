# utils/cleaners.py
# ─────────────────────────────────────────────────────────────
# WHAT THIS FILE IS:
#   Shared helper functions used by ALL scrapers.
#   Written once here. Every scraper imports from here.
#   No scraper ever duplicates these functions.
#
# RULE: Every function takes messy input → returns clean output.
# ─────────────────────────────────────────────────────────────

import re
from datetime import date


# ─────────────────────────────────────────────────────────────
# 1. CLEAN PRICE
# Input:  "$24.990" or "24990.00" or "$ 24.990,00"
# Output: 24990  (plain integer, no symbols)
# ─────────────────────────────────────────────────────────────
def clean_price(price_str):
    if not price_str:
        return None
    text = str(price_str).strip()
    # Remove currency symbols and spaces
    text = re.sub(r'[$ ]', '', text)
    # Handle decimal point — remove .00 style cents
    # "44900.00" → "44900"   "$24.990" → "24990"
    # The trick: if dot is followed by exactly 2 digits at end → cents, remove
    # If dot is used as thousands separator → remove dots only
    if re.search(r'\.\d{2}$', text):
        # Decimal notation: "44900.00" → remove the .00
        text = re.sub(r'\.\d+$', '', text)
    # Now remove all remaining non-digit characters (dots, commas)
    digits = re.sub(r'[^\d]', '', text)
    return int(digits) if digits else None


# ─────────────────────────────────────────────────────────────
# 2. EXTRACT ML
# Input:  "Lattafa Yara EDP 100ML Mujer"
# Output: 100  (integer)
# ─────────────────────────────────────────────────────────────
def extract_ml(text):
    if not text:
        return None
    match = re.search(r'(\d+)\s*ml', str(text), re.IGNORECASE)
    return int(match.group(1)) if match else None


# ─────────────────────────────────────────────────────────────
# 3. EXTRACT PERFUME TYPE
# Input:  "Lattafa Yara EDP 100ML"
# Output: "EDP"
# ─────────────────────────────────────────────────────────────
def extract_type(text):
    if not text:
        return "Unknown"
    match = re.search(
        r'\b(EDP Intense|EDT Intense|EDP|EDT|Parfum|Perfume|EDC)\b',
        str(text), re.IGNORECASE
    )
    return match.group(0).upper() if match else "Unknown"


# ─────────────────────────────────────────────────────────────
# 4. EXTRACT GENDER
# Input:  "Lattafa Yara EDP 100ML Mujer"
# Output: "Mujer"
# ─────────────────────────────────────────────────────────────
def extract_gender(text, tags=None):
    text = str(text) if text else ""
    tags = tags or []

    # Check the title text first
    if re.search(r'\bMujer\b|\bWoman\b|\bFemme\b|\bHer\b', text, re.IGNORECASE):
        return "Mujer"
    if re.search(r'\bHombre\b|\bMan\b|\bHomme\b|\bHim\b', text, re.IGNORECASE):
        return "Hombre"
    if re.search(r'\bUnisex\b|\bMixto\b', text, re.IGNORECASE):
        return "Unisex"

    # If not found in title, check tags (Shopify gives us these)
    for tag in tags:
        tag_lower = tag.lower()
        if any(w in tag_lower for w in ['mujer', 'woman', 'femme', 'her']):
            return "Mujer"
        if any(w in tag_lower for w in ['hombre', 'man', 'homme', 'him']):
            return "Hombre"
        if 'unisex' in tag_lower:
            return "Unisex"

    return "Unknown"


# ─────────────────────────────────────────────────────────────
# 5. GENERATE SKU
# Follows the client's pattern from the brief:
# "01LATGIVMMEDP75" → prefix + brand + product + type + ml
#
# Input:  brand="LATTAFA", name="GIVE ME GOURMAND", type="EDP", ml=75
# Output: "LATGIVMEDP75"
# ─────────────────────────────────────────────────────────────
def generate_sku(brand, product_name, perfume_type, ml):
    def abbreviate(text, length):
        # Take first N letters of each word, joined, uppercase
        if not text:
            return ""
        words = re.sub(r'[^a-zA-Z\s]', '', str(text)).split()
        return ''.join(w[:length].upper() for w in words)

    brand_code   = abbreviate(brand, 3)[:4]        # LAT
    product_code = abbreviate(product_name, 2)[:6]  # GIVME
    type_code    = str(perfume_type).upper()[:3]    # EDP
    ml_code      = str(ml) if ml else "00"          # 75

    return f"{brand_code}{product_code}{type_code}{ml_code}"


# ─────────────────────────────────────────────────────────────
# 6. TODAY'S DATE
# Output: "2026-05-24"  (string, for the scraped_at field)
# ─────────────────────────────────────────────────────────────
def today():
    return date.today().isoformat()


# ─────────────────────────────────────────────────────────────
# 7. BUILD PRODUCT ROW  ← THE MOST IMPORTANT FUNCTION
#
# This is the data contract enforcer.
# Every scraper calls this function to build its output row.
# No matter which scraper calls it, the output is always
# the same 12 fields in the same format.
#
# Input:  raw messy values from any scraper
# Output: one clean dictionary with exactly 12 fields
# ─────────────────────────────────────────────────────────────
def build_product_row(
    brand,
    product_name,
    variant=None,
    perfume_type=None,
    gender=None,
    ml=None,
    barcode=None,
    sale_price=None,
    original_price=None,
    available=True,
    source_site="",
    source_url="",
    tags=None,
):
    # Clean and normalize every field
    clean_brand        = str(brand).upper().strip() if brand else "Unknown"
    clean_name         = str(product_name).upper().strip() if product_name else "Unknown"
    clean_variant      = str(variant).upper().strip() if variant else None
    clean_type         = extract_type(perfume_type) if perfume_type else extract_type(product_name)
    clean_gender       = extract_gender(gender or product_name, tags)
    clean_ml           = ml if isinstance(ml, int) else extract_ml(str(ml) if ml else product_name)
    clean_sale         = clean_price(sale_price)
    clean_original     = clean_price(original_price)
    clean_sku          = generate_sku(clean_brand, clean_name, clean_type, clean_ml)

    # Return exactly 12 fields — always — no more, no less
    return {
        "sku":            clean_sku,
        "brand":          clean_brand,
        "product_name":   clean_name,
        "variant":        clean_variant,
        "perfume_type":   clean_type,
        "gender":         clean_gender,
        "ml":             clean_ml,
        "barcode":        barcode,
        "sale_price":     clean_sale,
        "original_price": clean_original,
        "available":      available,
        "source_site":    source_site,
        "source_url":     source_url,
        "scraped_at":     today(),
    }


# ─────────────────────────────────────────────────────────────
# QUICK TEST — run this file directly to verify it works
# python utils/cleaners.py
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing cleaners.py...\n")

    # Test clean_price
    assert clean_price("$24.990") == 24990
    assert clean_price("44900.00") == 44900
    assert clean_price(None) is None
    print("✓ clean_price works")

    # Test extract_ml
    assert extract_ml("Lattafa Yara EDP 100ML Mujer") == 100
    assert extract_ml("POLO SPORT EDT 125 ML") == 125
    assert extract_ml("No size here") is None
    print("✓ extract_ml works")

    # Test extract_type
    assert extract_type("Lattafa Yara EDP 100ML") == "EDP"
    assert extract_type("POLO SPORT EDT 125 ML") == "EDT"
    print("✓ extract_type works")

    # Test extract_gender
    assert extract_gender("Lattafa Yara EDP 100ML Mujer") == "Mujer"
    assert extract_gender("POLO SPORT EDT 125 ML Hombre") == "Hombre"
    assert extract_gender("CK One EDT 200ML Unisex") == "Unisex"
    print("✓ extract_gender works")

    # Test generate_sku
    sku = generate_sku("LATTAFA", "GIVE ME GOURMAND", "EDP", 75)
    print(f"✓ generate_sku: {sku}")

    # Test build_product_row — the full contract
    row = build_product_row(
        brand          = "Lattafa",
        product_name   = "Give Me Gourmand Mallow Madness EDP 75ML Mujer",
        sale_price     = "$24.990",
        original_price = "59990.00",
        available      = True,
        source_site    = "lodoro.cl",
        source_url     = "https://lodoro.cl/products/give-me-gourmand",
    )

    print("\n✓ build_product_row output:")
    for key, value in row.items():
        print(f"   {key:<18} → {value}")

    print("\n✓ All tests passed. cleaners.py is ready.")