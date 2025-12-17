"""
Evaluation script for SHL Assessment Recommendation System
Measures Mean Recall@K performance
"""

import pandas as pd
import numpy as np
import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from typing import List, Set, Dict

# Load catalog
catalog_path = Path(__file__).parent.parent / "api" / "final_catalog.json"
with open(catalog_path, 'r') as f:
    catalog = json.load(f)

# Create URL to index mapping
url_to_idx = {item['url'].strip().lower(): idx for idx, item in enumerate(catalog)}

# Initialize model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load embeddings
import torch
embed_path = Path(__file__).parent.parent / "api" / "embeddings.pt"
if embed_path.exists():
    embeddings = torch.load(embed_path)
else:
    print("ERROR: Embeddings not found. Please run Embed.py first.")
    exit(1)


def normalize_url(url: str) -> str:
    """Normalize URLs for matching"""
    return url.strip().lower().rstrip('/').replace('https://', '').replace('http://', '')


def get_recommendations(query: str, top_k: int = 10) -> List[str]:
    """Get top k recommendation URLs for a query"""
    q_emb = model.encode(query, convert_to_tensor=True, normalize_embeddings=True)
    scores = util.cos_sim(q_emb, embeddings)[0].cpu().numpy()
    
    # Get top k
    top_indices = scores.argsort()[-top_k:][::-1]
    
    recommendations = []
    for idx in top_indices:
        item = catalog[idx]
        recommendations.append(item['url'])
    
    return recommendations


def compute_recall_at_k(predicted: Set[str], ground_truth: Set[str], k: int = 10) -> float:
    """Compute Recall@K"""
    if len(ground_truth) == 0:
        return 0.0
    
    # Take only top k predictions
    predicted_k = list(predicted)[:k]
    
    # Count matches
    matches = sum(1 for p in predicted_k if normalize_url(p) in {normalize_url(g) for g in ground_truth})
    
    recall = matches / len(ground_truth)
    return recall


def evaluate_on_train_set(train_csv_path: str) -> Dict:
    """Evaluate on training set"""
    df = pd.read_csv(train_csv_path)
    
    # Group by query
    grouped = df.groupby('Query')['Assessment_url'].apply(lambda x: set(x)).to_dict()
    
    recall_at_10 = []
    recall_at_5 = []
    
    for query, ground_truth in grouped.items():
        predictions = get_recommendations(query, top_k=10)
        
        recall_10 = compute_recall_at_k(set(predictions), ground_truth, k=10)
        recall_5 = compute_recall_at_k(set(predictions), ground_truth, k=5)
        
        recall_at_10.append(recall_10)
        recall_at_5.append(recall_5)
        
        print(f"Query: {query[:50]}...")
        print(f"  Recall@10: {recall_10:.3f}, Recall@5: {recall_5:.3f}")
        print(f"  Ground truth: {len(ground_truth)} items")
        print()
    
    mean_recall_10 = np.mean(recall_at_10)
    mean_recall_5 = np.mean(recall_at_5)
    
    return {
        'mean_recall_10': mean_recall_10,
        'mean_recall_5': mean_recall_5,
        'recall_scores': recall_at_10
    }


def generate_test_predictions(test_csv_path: str, output_csv_path: str) -> None:
    """Generate predictions for test set"""
    df = pd.read_csv(test_csv_path)
    
    predictions = []
    for query in df['Query'].unique():
        recs = get_recommendations(query, top_k=10)
        
        for url in recs:
            predictions.append({
                'Query': query,
                'Assessment_url': url
            })
    
    # Save predictions
    pred_df = pd.DataFrame(predictions)
    pred_df.to_csv(output_csv_path, index=False)
    print(f"\nPredictions saved to {output_csv_path}")
    print(f"Total predictions: {len(pred_df)}")


if __name__ == "__main__":
    import sys
    
    train_path = Path(__file__).parent / "train.csv"
    test_path = Path(__file__).parent / "test.csv"
    output_path = Path(__file__).parent / "submission.csv"
    
    if train_path.exists():
        print("=" * 80)
        print("EVALUATING ON TRAINING SET")
        print("=" * 80)
        results = evaluate_on_train_set(str(train_path))
        print("\n" + "=" * 80)
        print(f"Mean Recall@10: {results['mean_recall_10']:.4f}")
        print(f"Mean Recall@5: {results['mean_recall_5']:.4f}")
        print("=" * 80)
    
    if test_path.exists():
        print("\nGenerating test predictions...")
        generate_test_predictions(str(test_path), str(output_path))
    else:
        print(f"Test set not found at {test_path}")
