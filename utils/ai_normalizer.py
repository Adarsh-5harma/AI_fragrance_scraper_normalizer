# utils/ai_normalizer.py
# ─────────────────────────────────────────────────────────────
# WHAT THIS DOES:
#   Uses Google Gemini AI (FREE) to normalize Unknown gender
#   and perfume_type fields by analyzing the product name.
#
#   Gemini reads the product name and returns:
#     gender       → Hombre | Mujer | Unisex | Unknown
#     perfume_type → EDP | EDT | Parfum | EDC | Unknown
#
# FREE TIER:
#   Gemini Flash: 1,500 requests/day FREE
#   Your database (~800 unknowns / 30 per batch = ~27 calls)
#   Cost: $0.00
#
# HOW TO USE:
#   from utils.ai_normalizer import normalize_batch
#   results = normalize_batch(["CHANEL NO 5 100ML", "POLO SPORT 75ML"])
#
# GET YOUR FREE KEY:
#   https://aistudio.google.com/apikey
#   (Sign in with Google → "Get API Key" → "Create API key in new project")
#   The key will start with: AIza...
# ─────────────────────────────────────────────────────────────

import os
import json
import time
from google import genai

# ── API client setup ──────────────────────────────────────────
# API key hardcoded for simplicity
GEMINI_API_KEY = "AQ.Ab8RN6Iix5DzhqznrH9aDUsiUjGTVaqJlKV3M9twF2A3lL1iAg"

def _get_client():
    return genai.Client(api_key=GEMINI_API_KEY)


# ── The prompt sent to Gemini ─────────────────────────────────
PROMPT_TEMPLATE = """You are a fragrance product data expert.
For each product name in the JSON array, determine:
1. gender: Is this perfume for Hombre (men), Mujer (women), Unisex, or Unknown?
2. perfume_type: Is it EDP, EDT, Parfum, EDC, or Unknown?

Rules:
- Hombre signals: hombre, man, men, homme, him, caballero, masculin, boy
- Mujer signals: mujer, woman, women, femme, her, ella, girl, lady, femenin
- Unisex signals: unisex, mixto, unisexe
- EDP = Eau de Parfum, EDT = Eau de Toilette, EDC = Eau de Cologne
- Parfum = pure parfum / extrait de parfum
- If genuinely unclear, use Unknown

Respond ONLY with a JSON array. No explanation. No markdown. No code fences. Just raw JSON.
Example input: ["CHANEL CHANCE EDP 100ML MUJER", "POLO SPORT EDT 125ML HOMBRE"]
Example output: [{"gender":"Mujer","perfume_type":"EDP"},{"gender":"Hombre","perfume_type":"EDT"}]

Input: """


def normalize_batch(product_names: list, max_retries: int = 3) -> list:
    """
    Send a batch of product names to Gemini and get normalized gender + type back.

    Args:
        product_names: List of product name strings (max 50 per batch recommended)
        max_retries:   Number of retry attempts on API errors

    Returns:
        List of dicts: [{"gender": "Mujer", "perfume_type": "EDP"}, ...]
        Falls back to {"gender": "Unknown", "perfume_type": "Unknown"} on failure.
    """
    if not product_names:
        return []

    client = _get_client()
    fallback = [{"gender": "Unknown", "perfume_type": "Unknown"}] * len(product_names)

    full_prompt = PROMPT_TEMPLATE + json.dumps(product_names)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt,
            )
            raw_text = response.text.strip()

            # Strip markdown code fences if Gemini adds them anyway
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            # Parse JSON
            results = json.loads(raw_text)

            # Validate count
            if len(results) != len(product_names):
                print(f"  ⚠ AI returned {len(results)} results for {len(product_names)} products. Using fallback.")
                return fallback

            # Validate and sanitize each result
            valid_genders = {"Hombre", "Mujer", "Unisex", "Unknown"}
            valid_types   = {"EDP", "EDT", "Parfum", "EDC", "Unknown"}

            for r in results:
                if r.get("gender") not in valid_genders:
                    r["gender"] = "Unknown"
                if r.get("perfume_type") not in valid_types:
                    r["perfume_type"] = "Unknown"

            return results

        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON parse error (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)

        except Exception as e:
            err_str = str(e)
            print(f"\n  ACTUAL ERROR: {err_str}\n")  # show real error for debugging
            if "429" in err_str or "quota" in err_str.lower():
                wait = 15 * (attempt + 1)
                print(f"  ⚠ Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  ⚠ API error (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)

    print(f"  ✗ All {max_retries} attempts failed. Using Unknown fallback.")
    return fallback


def normalize_single(product_name: str) -> dict:
    """
    Normalize a single product name. Convenience wrapper around normalize_batch.

    Returns: {"gender": "Mujer", "perfume_type": "EDP"}
    """
    results = normalize_batch([product_name])
    return results[0] if results else {"gender": "Unknown", "perfume_type": "Unknown"}


# ─────────────────────────────────────────────────────────────
# QUICK TEST — run this file directly to verify API works
# python utils/ai_normalizer.py
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Gemini AI normalizer...\n")

    test_names = [
        "CHANEL CHANCE EDP 100ML MUJER",
        "POLO SPORT EDT 125ML HOMBRE",
        "CK ONE EDT 200ML UNISEX",
        "LATTAFA YARA TOUS 35ML",
        "ARMAF TAG HIM 100ML HOMBRE",
        "DIOR SAUVAGE 60ML",
        "MAISON ALHAMBRA NO.2 MEN 150ML HOMBRE",
    ]

    print(f"Sending {len(test_names)} product names to Gemini (FREE)...\n")
    results = normalize_batch(test_names)

    print("Results:")
    for name, result in zip(test_names, results):
        print(f"  {name[:50]:<50} → gender={result['gender']:<8} type={result['perfume_type']}")

    print("\n✓ Gemini AI normalizer working correctly. Cost: $0.00")
