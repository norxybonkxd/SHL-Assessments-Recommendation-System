import requests
from bs4 import BeautifulSoup
import json
import re
import time
from pathlib import Path

base_url = "https://www.shl.com"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

catalog = []
scraped_urls = set()

# Scrape individual test solutions (type=1)
print("Scraping individual test solutions...")
for page in range(50):  # Increase range to get all items
    start = page * 12
    url = f"https://www.shl.com/products/product-catalog/?start={start}&type=1"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"Skip page {page}: {resp.status_code}")
            continue
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        links = soup.find_all('a', href=re.compile(r'/products/product-catalog/view/'))
        
        if not links:
            print(f"No more items found at page {page}")
            break
            
        for link in links:
            href = link.get('href', '')
            if '/view/' not in href or href in scraped_urls:
                continue
            name = link.get_text(strip=True)
            if not name:
                continue
            
            full_url = base_url + href if href.startswith('/') else href
            scraped_urls.add(href)
            
            print(f"Scraping: {name[:50]}... | URL: {full_url}")
            
            try:
                view_resp = requests.get(full_url, headers=headers, timeout=10)
                view_soup = BeautifulSoup(view_resp.text, 'html.parser')
                
                # Extract title
                title_name = view_soup.title.text.split(' | ')[0].strip() if view_soup.title else name
                
                # Extract description
                desc_elem = view_soup.find(lambda tag: tag.name in ['h4', 'h5', 'h3'] and 'Description' in tag.get_text()) if view_soup else None
                description = ''
                if desc_elem:
                    next_p = desc_elem.find_next_sibling('p')
                    description = ' '.join(next_p.stripped_strings) if next_p else ''
                
                # Extract test type
                test_type = ''
                if not test_type and view_soup:
                    test_match = re.search(r'Test Type:\s*([A-Z])', view_soup.get_text(), re.I)
                    test_type = test_match.group(1).upper() if test_match else ''
                
                # Extract job levels
                job_elem = view_soup.find(lambda tag: tag.name in ['h4', 'h5'] and 'Job levels' in tag.get_text()) if view_soup else None
                job_levels = ''
                if job_elem:
                    next_p = job_elem.find_next_sibling('p')
                    job_levels = ', '.join(next_p.stripped_strings) if next_p else ''
                
                # Extract languages
                lang_elem = view_soup.find(lambda tag: tag.name in ['h4', 'h5'] and 'Languages' in tag.get_text()) if view_soup else None
                languages = ''
                if lang_elem:
                    next_p = lang_elem.find_next_sibling('p')
                    languages = ', '.join(next_p.stripped_strings) if next_p else ''
                
                # Extract duration
                length_match = re.search(r'Completion Time in minutes\s*=\s*(\d+)', view_soup.get_text()) if view_soup else None
                length = length_match.group(1) if length_match else ''
                
                # Extract remote support
                remote = 'Yes' if view_soup and 'Remote Testing:' in view_soup.get_text() else 'No'
                
                # Extract adaptive support
                adaptive = 'Yes' if view_soup and 'Adaptive' in view_soup.get_text() else 'No'
                
                # Build categories
                categories = []
                if description:
                    categories = [t.strip() for t in re.split(r'[,;]', description) if len(t.strip()) > 5][:5]
                
                catalog.append({
                    'name': title_name,
                    'url': full_url,
                    'description': description[:500],
                    'test_type': test_type,
                    'job_levels': job_levels,
                    'languages': languages,
                    'length_minutes': length,
                    'remote_testing': remote,
                    'adaptive_support': adaptive,
                    'categories': categories
                })
                
                time.sleep(1)
            except Exception as e:
                print(f"Error scraping {full_url}: {e}")
                time.sleep(1)
    
    time.sleep(2)

# Save catalog
output_path = Path(__file__).parent.parent / "api" / "final_catalog.json"
with open(output_path, 'w') as f:
    json.dump(catalog, f, indent=2)
    
print(f"\nFinal: {len(catalog)} assessments scraped")
print(f"Test types found: {set(i['test_type'] for i in catalog if i['test_type'])}")
print(f"Catalog saved to {output_path}")
