# discover_shopify_sites.py
import requests
import json

def check_shopify_site(domain, paths_to_check):
    """Check if a site uses Shopify API"""
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print(f"\n🔍 Testing: {domain}")
    print("-" * 50)
    
    for path in paths_to_check:
        url = f"https://{domain}{path}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'products' in data:
                        product_count = len(data.get('products', []))
                        print(f"  ✅ FOUND: {path}")
                        print(f"     Products: {product_count}")
                        if product_count > 0:
                            sample = data['products'][0].get('title', 'N/A')[:50]
                            print(f"     Sample: {sample}")
                        return True
                    elif 'collection' in data:
                        print(f"  ✅ FOUND: {path} (collection endpoint)")
                        return True
                except:
                    print(f"  ⚠️ {path} - Not JSON or unexpected format")
            else:
                print(f"  ❌ {path} - HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ {path} - Error: {str(e)[:50]}")
    
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("CHILEAN PERFUME SHOPIFY SITE DISCOVERY")
    print("=" * 60)
    
    # Sites that might use Shopify
    candidate_sites = [
        # From your earlier test - already working
        "www.lodoro.cl",
        
        # Other potential Shopify sites
        "www.perfumeria.cl",
        "www.perfumes.cl",
        "www.fraiche.cl",
        "www.aromashop.cl",
        "www.esencia.cl",
        "www.scent.cl",
        "www.olfato.cl",
        "www.perfumeschile.cl",
        "www.mundoperfume.cl",
        "www.perfumesfactory.cl",
        "www.elperfumista.cl",
        "www.essence.cl",
        
        # Department stores (likely NOT Shopify, but check anyway)
        "www.paris.cl",
        "www.ripley.cl",
        "www.falabella.cl",
    ]
    
    paths = [
        "/products.json",
        "/collections/all/products.json", 
        "/search.json",
        "/cart.js"  # Another Shopify indicator
    ]
    
    results = {}
    for site in candidate_sites:
        is_shopify = check_shopify_site(site, paths)
        results[site] = is_shopify
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    working = [site for site, status in results.items() if status]
    not_working = [site for site, status in results.items() if not status]
    
    print(f"\n✅ Shopify sites found ({len(working)}):")
    for site in working:
        print(f"  • {site}")
    
    print(f"\n❌ Not Shopify / API not found ({len(not_working)}):")
    for site in not_working[:10]:  # Show first 10
        print(f"  • {site}")