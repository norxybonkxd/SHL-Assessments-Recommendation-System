import json
import os
import re
from pathlib import Path
from typing import List, Dict

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer, util

BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"
CATALOG_PATH = BASE_DIR / "final_catalog.json"
EMBED_PATH = BASE_DIR / "embeddings.pt"

app = FastAPI(title="SHL Recommender")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = SentenceTransformer("all-MiniLM-L6-v2")

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    catalog: List[dict] = json.load(f)

print(f"Loaded {len(catalog)} assessments from catalog")


def _item_text(item: dict) -> str:
    """Create rich text representation for embedding"""
    parts = [
        item.get("name", ""),
        item.get("name", ""),  # Weight important field
        item.get("description", ""),
        f"Type: {item.get('test_type', '')}",
        f"Job Levels: {item.get('job_levels', '')}",
        item.get("job_levels", ""),  # Weight important field
        f"Remote: {item.get('remote_testing', '')}",
    ]
    return " ".join([p for p in parts if p])


# Load or generate embeddings
if EMBED_PATH.exists():
    embeddings = torch.load(EMBED_PATH)
    print(f"Loaded embeddings with shape {embeddings.shape}")
else:
    print("Generating embeddings...")
    texts = [_item_text(it) for it in catalog]
    embeddings = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    torch.save(embeddings, EMBED_PATH)
    print(f"Saved embeddings with shape {embeddings.shape}")


def detect_skill_domains(query: str) -> Dict[str, List[str]]:
    """Detect technical and soft skills from query"""
    query_lower = query.lower()
    
    # Technical skills
    tech_keywords = {
        'java', 'python', 'javascript', 'sql', 'c++', 'csharp', '.net', 'golang',
        'react', 'angular', 'vue', 'aws', 'azure', 'kubernetes', 'docker',
        'html', 'css', 'frontend', 'backend', 'fullstack', 'devops'
    }
    
    # Soft skills  
    soft_keywords = {
        'collaborate', 'collaboration', 'communication', 'teamwork', 'team',
        'leadership', 'personality', 'behavior', 'emotional', 'intelligence',
        'interpersonal', 'management', 'stakeholder', 'adaptability'
    }
    
    detected_tech = [k for k in tech_keywords if k in query_lower]
    detected_soft = [k for k in soft_keywords if k in query_lower]
    
    return {'tech': detected_tech, 'soft': detected_soft}


def get_balanced_recommendations(query: str, top_k: int = 10) -> List[Dict]:
    """Get balanced recommendations across skill domains"""
    
    skills = detect_skill_domains(query)
    needs_technical = len(skills['tech']) > 0
    needs_soft = len(skills['soft']) > 0
    
    # Encode query with skill indicators
    query_augmented = query
    if detected_tech := skills['tech']:
        query_augmented += " " + " ".join(detected_tech)
    if detected_soft := skills['soft']:
        query_augmented += " " + " ".join(detected_soft)
    
    q_emb = model.encode(query_augmented, convert_to_tensor=True, normalize_embeddings=True)
    scores = util.cos_sim(q_emb, embeddings)[0].cpu().numpy()
    
    # Get top candidates
    top_indices = scores.argsort()[-top_k * 2:][::-1]
    
    recommendations = []
    technical_count = 0
    soft_count = 0
    max_per_type = top_k // 2 if (needs_technical and needs_soft) else top_k
    
    for idx in top_indices:
        if len(recommendations) >= top_k:
            break
        
        item = catalog[idx]
        test_type = item.get("test_type", "").upper()
        
        # Balance: if both tech and soft skills needed, split recommendations
        if needs_technical and needs_soft:
            if test_type in ['K', 'S']:  # Knowledge/Technical or Simulations
                if technical_count >= max_per_type:
                    continue
                technical_count += 1
            elif test_type == 'P':  # Personality/Behavior
                if soft_count >= max_per_type:
                    continue
                soft_count += 1
        
        recommendations.append({
            "name": item.get("name"),
            "url": item.get("url"),
            "description": (item.get("description") or "")[:240],
            "score": float(scores[idx]),
            "test_type": test_type,
            "job_levels": item.get("job_levels", ""),
            "adaptive_support": item.get("adaptive_support", ""),
            "remote_testing": item.get("remote_testing", ""),
        })
    
    return recommendations


class RecommendRequest(BaseModel):
    query: str = Field(..., description="Free text, JD text, or JD URL")
    top_k: int = Field(default=10, ge=5, le=10, description="Number of results (5-10)")


@app.get("/health")
async def health():
    return {"status": "healthy", "items": len(catalog)}


@app.post("/recommend")
async def recommend(body: RecommendRequest):
    text = body.query.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Query required")
    
    # If it's a URL, try to extract text
    if text.startswith("http"):
        try:
            import requests
            resp = requests.get(text, timeout=5)
            text = resp.text[:2000]
        except:
            pass
    
    recs = get_balanced_recommendations(text, top_k=body.top_k)
    
    if not recs:
        raise HTTPException(status_code=400, detail="No recommendations found")
    
    return {"recommended_assessments": recs}


@app.get("/")
async def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)


if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

