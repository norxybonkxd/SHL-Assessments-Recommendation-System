import pandas as pd
import json

# Load
train = pd.read_csv('train.csv').groupby('Query')['Assessment_url'].apply(lambda x: list(x.unique())).reset_index()
with open('final_catalog.json') as f:
    catalog = json.load(f)

# Compare URLs
print("=== GT URL Sample ===")
gt_sample = train.iloc[0]['Assessment_url'][0]
print(gt_sample)

print("\n=== Catalog URL Sample ===")
cat_sample = catalog[0]['url']
print(cat_sample)

print("\n=== Catalog All URL Patterns ===")
patterns = set()
for item in catalog[:10]:
    url = item['url']
    if '/solutions/' in url:
        patterns.add('/solutions/')
    if '/products/' in url and '/solutions/' not in url:
        patterns.add('/products/ (no solutions)')
print(patterns)

print("\n=== Check if ANY GT in Catalog ===")
catalog_urls = {item['url'] for item in catalog}
gt_urls = set()
for urls in train['Assessment_url']:
    gt_urls.update(urls)

matches = gt_urls & catalog_urls
print(f"GT URLs: {len(gt_urls)}")
print(f"Catalog URLs: {len(catalog_urls)}")
print(f"Direct matches: {len(matches)}")

if len(matches) == 0:
    print("\n❌ ZERO OVERLAP - URL Format Issue!")
    print("Sample GT:", list(gt_urls)[:3])
    print("Sample Cat:", list(catalog_urls)[:3])
