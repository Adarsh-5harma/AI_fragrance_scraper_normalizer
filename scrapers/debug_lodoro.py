# debug_lodoro.py - Debug the Shopify API response
import requests

SOURCE_SITE = 'lodoro.cl'
BASE_URL = "https://www.lodoro.cl/collections/all/products.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-CL,es;q=0.9",
}

print("=" * 60)
print("DEBUGGING LODORO.CL API")
print("=" * 60)

# Try 1: Simple request without fancy headers
print("\n1. Testing basic request...")
try:
    response = requests.get(BASE_URL, timeout=10)
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
    print(f"   First 200 chars of response:")
    print(f"   {response.text[:200]}...")
    
    if response.status_code == 200:
        # Try to parse as JSON
        try:
            data = response.json()
            print(f"\n   ✓ SUCCESS! JSON parsed correctly")
            print(f"   Number of products: {len(data.get('products', []))}")
        except:
            print(f"\n   ✗ Response is NOT valid JSON")
            print(f"   Response appears to be: {response.text[:500]}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Try 2: With all headers (what you were using)
print("\n2. Testing with full headers...")
try:
    full_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        "Referer": "https://www.lodoro.cl/collections/perfumes",
        "X-Requested-With": "XMLHttpRequest",
    }
    response = requests.get(BASE_URL, headers=full_headers, timeout=10)
    print(f"   Status Code: {response.status_code}")
    print(f"   First 200 chars:")
    print(f"   {response.text[:200]}...")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Try 3: Check if the website is using a different Shopify pattern
print("\n3. Testing alternative endpoints...")
alternatives = [
    "https://www.lodoro.cl/products.json",
    "https://www.lodoro.cl/collections/all.json",
    "https://www.lodoro.cl/search.json",
]

for alt_url in alternatives:
    try:
        response = requests.get(alt_url, timeout=10)
        if response.status_code == 200:
            print(f"   ✓ {alt_url} → Status {response.status_code}")
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"     Valid JSON! Keys: {list(data.keys())}")
            except:
                print(f"     Response: {response.text[:100]}...")
        else:
            print(f"   ✗ {alt_url} → Status {response.status_code}")
    except Exception as e:
        print(f"   ✗ {alt_url} → Error: {e}")

# Try 4: Check if the store uses password protection
print("\n4. Checking if store is password-protected...")
try:
    response = requests.get("https://www.lodoro.cl", timeout=10)
    if "password" in response.text.lower() or "store is password protected" in response.text.lower():
        print("   ⚠ WARNING: Store appears to be password protected!")
        print(f"   Response snippet: {response.text[:300]}")
    else:
        print("   ✓ Store appears to be public")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)