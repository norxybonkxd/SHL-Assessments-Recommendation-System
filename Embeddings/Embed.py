import json
import numpy as np
import torch
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load catalog
catalog_path = Path(__file__).parent.parent / "api" / "final_catalog.json"
with open(catalog_path, 'r') as f:
    catalog = json.load(f)

print(f"Loaded {len(catalog)} assessments")

# Create rich text representations for embedding
texts = []
for item in catalog:
    name = item.get('name', '').strip()
    desc = item.get('description', '').strip()[:800]
    test_type = item.get('test_type', '').strip()
    job_levels = item.get('job_levels', '').strip()
    remote = item.get('remote_testing', '').strip()
    adaptive = item.get('adaptive_support', '').strip()
    
    # Create text with weights on important fields
    text = f"{name} {name} {desc} Test Type: {test_type} Job Levels: {job_levels} Remote: {remote} Adaptive: {adaptive}"
    texts.append(text)

# Generate embeddings
print("Generating embeddings...")
embeddings = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)

# Save embeddings as torch
embeddings_path = Path(__file__).parent.parent / "api" / "embeddings.pt"
torch.save(embeddings, embeddings_path)
print(f"Saved embeddings to {embeddings_path} with shape {embeddings.shape}")

# Also save as numpy for compatibility
embeddings_npy = embeddings.cpu().numpy()
embeddings_npy_path = Path(__file__).parent.parent / "api" / "embeddings.npy"
np.save(embeddings_npy_path, embeddings_npy)

# Save cleaned catalog
catalog_npy_path = Path(__file__).parent.parent / "api" / "catalog.npy"
np.save(catalog_npy_path, np.array(catalog, dtype=object))

print(f"Complete! Embedded {len(catalog)} assessments successfully")
