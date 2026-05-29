# test_connection.py
# Test connections to all configured sites

import requests
import yaml
import os

def load_config():
    """Load sites from YAML config"""
    config_path = 'config/sites.yaml'
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        return {}
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('sites', {})

def test_site_connection(site_name, site_config):
    """Test if a site's API is accessible"""
    url = site_config['url'] + site_config['api_endpoint']
    headers = site_config.get('headers', {})
    
    print(f"\n🔍 Testing: {site_name} ({site_config['url']})")
    print("-" * 50)
    
    try:
        response = requests.get(f"{url}?limit=1", headers=headers, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                products = data.get('products', [])
                if products:
                    sample = products[0].get('title', 'Unknown')[:50]
                    print(f"  ✅ API accessible!")
                    print(f"  Status: {response.status_code}")
                    print(f"  Sample: {sample}")
                    return True
                else:
                    print(f"  ⚠️ API accessible but no products")
                    return False
            except:
                print(f"  ❌ JSON parse error")
                print(f"  Response: {response.text[:100]}")
                return False
        else:
            print(f"  ❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Connection error: {str(e)[:100]}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("SITE CONNECTION TESTER")
    print("="*60)
    
    sites = load_config()
    
    results = {}
    for name, config in sites.items():
        if config.get('enabled', True):
            results[name] = test_site_connection(name, config)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    working = [name for name, result in results.items() if result]
    failed = [name for name, result in results.items() if not result]
    
    print(f"\n✅ Working: {len(working)}")
    for name in working:
        print(f"  • {name}")
    
    print(f"\n❌ Failed: {len(failed)}")
    for name in failed:
        print(f"  • {name}")