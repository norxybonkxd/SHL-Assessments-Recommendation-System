import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from rank_bm25 import BM25Okapi
import json
import os
import re

train = pd.read_csv('train.csv').groupby('Query')['Assessment_url'].apply(lambda x: ';'.join(x.unique())).reset_index(name='ground_truth_urls')
with open('final_catalog.json') as f:
    catalog = json.load(f)

def normalize_url(url):
    return url.strip().lower().rstrip('/').split('/')[-1]

model = SentenceTransformer('all-mpnet-base-v2')

def extract_keywords(query):
    tech = re.findall(r'\b(java|python|sql|javascript|selenium|\.net|excel|c\+\+|html|css)\b', query, re.I)
    soft = re.findall(r'\b(collaborat\w*|communicat\w*|leadership|teamwork|interpersonal|personality|behavior)\b', query, re.I)
    return {'tech': set([k.lower() for k in tech]), 'soft': set([k.lower() for k in soft])}

def item_text(item):
    name = item.get('name', '')
    desc = item.get('description', '')[:1200]
    type_map = {'K':'technical programming coding', 'P':'personality behavior soft-skills communication teamwork', 'S':'leadership management simulation'}
    return f"{name} {name} {desc} {type_map.get(item.get('test_type',''),'')} {item.get('job_levels','')}"

texts = [item_text(item) for item in catalog]
embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

# BM25
tokenized = [t.lower().split() for t in texts]
bm25 = BM25Okapi(tokenized)

def get_top10_balanced(query):
    kw = extract_keywords(query)
    needs_soft = len(kw['soft']) > 0 or 'collaborate' in query.lower() or 'team' in query.lower()
    
    # Scores
    q_emb = model.encode(f"{query} {' '.join(kw['tech'])} {' '.join(kw['soft'])}", normalize_embeddings=True)
    sem_scores = util.cos_sim(q_emb, embeddings)[0].cpu().numpy()
    bm25_scores = bm25.get_scores(query.lower().split())
    
    combined = 0.6 * sem_scores + 0.4 * (bm25_scores / (bm25_scores.max() + 1e-6))
    
    # Keyword boost
    for i, item in enumerate(catalog):
        item_lower = (item['name'] + ' ' + item.get('description','')).lower()
        for kw_tech in kw['tech']:
            if kw_tech in item_lower:
                combined[i] += 0.25
        for kw_soft in kw['soft']:
            if kw_soft in item_lower:
                combined[i] += 0.3
    
    # Get top 20, then diversify
    top20_idx = np.argsort(combined)[-20:][::-1]
    
    # Diversify: if needs_soft, ensure P/S types
    results = []
    k_items = [i for i in top20_idx if catalog[i].get('test_type') == 'K']
    p_items = [i for i in top20_idx if catalog[i].get('test_type') in ['P', 'S', 'B']]
    other = [i for i in top20_idx if i not in k_items and i not in p_items]
    
    if needs_soft:
        # 50/50 mix
        results = p_items[:5] + k_items[:5]
        results = results[:10]
    else:
        results = k_items[:7] + p_items[:3]
    
    results = (results + list(top20_idx))[:10]  # Fill to 10
    return [catalog[i]['url'] for i in results]

# Eval
total_recall = 0
for idx, row in train.iterrows():
    gt_slugs = {normalize_url(u) for u in row['ground_truth_urls'].split(';') if u.strip()}
    pred_urls = get_top10_balanced(row['Query'])
    pred_slugs = {normalize_url(u) for u in pred_urls}
    
    hits = len(gt_slugs & pred_slugs)
    recall = hits / len(gt_slugs) if len(gt_slugs) > 0 else 0
    total_recall += recall
    print(f"Q{idx+1}: Recall={recall:.2f} ({hits}/{len(gt_slugs)})")

print(f"\n* Mean Recall@10: {total_recall/len(train):.3f}")
