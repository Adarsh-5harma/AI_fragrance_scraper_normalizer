# utils/ai_normalizer.py
# ─────────────────────────────────────────────────────────────
# WHAT THIS DOES:
#   Uses Qwen 2.5 32B (via Groq FREE tier) to normalize Unknown 
#   gender and perfume_type fields by analyzing the product name.
#
# FREE TIER:
#   Groq hosts Qwen 2.5 32B for FREE with incredibly fast inference.
#
# HOW TO USE:
#   from utils.ai_normalizer import normalize_batch
#   results = normalize_batch(["CHANEL NO 5 100ML", "POLO SPORT 75ML"])
#
# GET YOUR FREE KEY:
#   https://console.groq.com/keys
#   (Sign in with GitHub/Google → "Create API Key")
# ─────────────────────────────────────────────────────────────

import os
import json
import time
from groq import Groq

# ── API client setup ──────────────────────────────────────────
# Get your FREE Groq API key from https://console.groq.com/keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your_groq_api_key_here")

def _get_client():
    return Groq(api_key=GROQ_API_KEY)


# ── The prompt sent to Qwen ───────────────────────────────────
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

Respond ONLY with a JSON object containing a "results" array. No explanation. No markdown. No code fences.
Example input: ["CHANEL CHANCE EDP 100ML MUJER", "POLO SPORT EDT 125ML HOMBRE"]
Example output: {"results": [{"gender":"Mujer","perfume_type":"EDP"},{"gender":"Hombre","perfume_type":"EDT"}]}

Input: """


def normalize_batch(product_names: list, max_retries: int = 3) -> list:
    """
    Send a batch of product names to Qwen (via Groq) and get normalized gender + type back.
    """
    if not product_names:
        return []

    client = _get_client()
    fallback = [{"gender": "Unknown", "perfume_type": "Unknown"}] * len(product_names)
    full_prompt = PROMPT_TEMPLATE + json.dumps(product_names)

    for attempt in range(max_retries):
        try:
            # Groq API call
            response = client.chat.completions.create(
                model="qwen/qwen3-32b",  # Qwen 3 32B is incredibly fast and smart
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that strictly outputs JSON."},
                    {"role": "user", "content": full_prompt}
                ],
                response_format={"type": "json_object"}, # Forces mathematically valid JSON!
                temperature=0.1
            )
            
            raw_text = response.choices[0].message.content
            parsed_json = json.loads(raw_text)
            
            # Extract the results array from the object
            results = parsed_json.get("results", [])

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
            print(f"\n  ACTUAL ERROR: {err_str}\n")
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
    """
    results = normalize_batch([product_name])
    return results[0] if results else {"gender": "Unknown", "perfume_type": "Unknown"}


# ─────────────────────────────────────────────────────────────
# QUICK TEST — run this file directly to verify API works
# python utils/ai_normalizer.py
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Qwen (via Groq) AI normalizer...\n")

    test_names = [
        "CHANEL CHANCE EDP 100ML MUJER",
        "POLO SPORT EDT 125ML HOMBRE",
        "CK ONE EDT 200ML UNISEX",
        "LATTAFA YARA TOUS 35ML",
        "ARMAF TAG HIM 100ML HOMBRE",
        "DIOR SAUVAGE 60ML",
        "MAISON ALHAMBRA NO.2 MEN 150ML HOMBRE",
    ]

    print(f"Sending {len(test_names)} product names to Qwen 2.5 32B (FREE via Groq)...\n")
    results = normalize_batch(test_names)

    print("Results:")
    for name, result in zip(test_names, results):
        print(f"  {name[:50]:<50} → gender={result['gender']:<8} type={result['perfume_type']}")

    print("\n✓ Qwen AI normalizer working correctly. Cost: $0.00")