# utils/run_all.py
# Run all scrapers and combine data

import sys
import os
import subprocess
import pandas as pd
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# List of scrapers to run (order by priority)
SCRAPERS = [
    'lodoro',      # Working ✅
    'multimarcas', # To test
    # Add more as you create them:
    # 'paris',
    # 'ripley',
    # 'falabella',
]

def run_single_scraper(scraper_name):
    """Run a single scraper and return result"""
    print(f"\n{'='*60}")
    print(f"Running: {scraper_name}.py")
    print('='*60)
    
    script_path = os.path.join('scrapers', f'{scraper_name}.py')
    
    if not os.path.exists(script_path):
        print(f"❌ Scraper {scraper_name}.py not found")
        return None
    
    try:
        result = subprocess.run(
            ['python', script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            'name': scraper_name,
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'timestamp': datetime.now().isoformat()
        }
    except subprocess.TimeoutExpired:
        return {
            'name': scraper_name,
            'success': False,
            'error': 'Timeout after 5 minutes',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'name': scraper_name,
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def run_all_scrapers():
    """Run all configured scrapers"""
    results = []
    
    print("\n" + "="*60)
    print("PERFUME MARKET SCRAPER - BATCH RUN")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    for scraper in SCRAPERS:
        result = run_single_scraper(scraper)
        if result:
            results.append(result)
            
            if result['success']:
                print(f"\n✅ {scraper} completed successfully")
            else:
                print(f"\n❌ {scraper} failed")
                if 'error' in result:
                    print(f"   Error: {result['error'][:200]}")
    
    return results

def merge_all_data():
    """Merge all CSV files into a single master file"""
    print("\n" + "="*60)
    print("MERGING DATA FROM ALL SCRAPERS")
    print("="*60)
    
    data_dir = 'data'
    all_data = []
    files_loaded = []
    
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return None
    
    # Find all CSV files (excluding backups and master)
    for file in os.listdir(data_dir):
        if file.endswith('_raw.csv') and not file.startswith('master'):
            filepath = os.path.join(data_dir, file)
            try:
                df = pd.read_csv(filepath)
                df['source_file'] = file
                df['source_site_clean'] = file.replace('_raw.csv', '')
                all_data.append(df)
                files_loaded.append(f"{file} ({len(df)} rows)")
                print(f"✅ Loaded {len(df):,} rows from {file}")
            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
    
    if not all_data:
        print("❌ No data files found")
        return None
    
    # Combine all data
    master_df = pd.concat(all_data, ignore_index=True)
    
    # Remove duplicates based on SKU (keep first occurrence)
    initial_count = len(master_df)
    master_df = master_df.drop_duplicates(subset=['sku'], keep='first')
    duplicates_removed = initial_count - len(master_df)
    
    # Save master file
    master_file = f'data/master_all_sites_{datetime.now().strftime("%Y%m%d")}.csv'
    master_df.to_csv(master_file, index=False)
    
    # Also save as latest
    master_df.to_csv('data/master_all_sites_latest.csv', index=False)
    
    print("\n" + "="*60)
    print("MERGE SUMMARY")
    print("="*60)
    print(f"Files loaded: {len(files_loaded)}")
    for f in files_loaded:
        print(f"  • {f}")
    print(f"\nTotal rows before dedup: {initial_count:,}")
    print(f"Duplicates removed: {duplicates_removed:,}")
    print(f"Unique products: {len(master_df):,}")
    print(f"\nMaster file saved: {master_file}")
    print(f"Latest master: data/master_all_sites_latest.csv")
    
    # Show brand statistics
    print("\n📊 TOP 10 BRANDS:")
    brand_counts = master_df['brand'].value_counts().head(10)
    for brand, count in brand_counts.items():
        print(f"  {brand}: {count:,} products")
    
    return master_df

def generate_report(results):
    """Generate a summary report"""
    print("\n" + "="*60)
    print("BATCH RUN REPORT")
    print("="*60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n✅ Successful scrapers: {len(successful)}")
    for r in successful:
        print(f"  • {r['name']}")
    
    print(f"\n❌ Failed scrapers: {len(failed)}")
    for r in failed:
        print(f"  • {r['name']}")
        if 'error' in r and r['error']:
            print(f"    Error: {r['error'][:100]}")
    
    # Save report
    report_file = f'logs/batch_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    os.makedirs('logs', exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_scrapers': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        }, f, indent=2)
    
    print(f"\n📄 Report saved: {report_file}")

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("PERFUME MARKET INTELLIGENCE PLATFORM")
    print("Phase 1 - Multi-Site Scraper")
    print("="*60)
    
    # Step 1: Run all scrapers
    results = run_all_scrapers()
    
    # Step 2: Generate report
    generate_report(results)
    
    # Step 3: Merge all data
    master_data = merge_all_data()
    
    # Step 4: Final summary
    print("\n" + "="*60)
    print("BATCH COMPLETE")
    print("="*60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Check 'data/master_all_sites_latest.csv' for combined data")
    print(f"Check 'logs/' for detailed logs")

if __name__ == "__main__":
    main()