# SHL Assessment Recommendation System

## Overview
This is an intelligent recommendation system that suggests relevant SHL assessments based on job descriptions or natural language queries. The system uses modern LLM embeddings and semantic search to match job requirements with appropriate assessment tools.
## 🔗 Links

- **Web App**: https://norxynorzy-shl-recommender.hf.space
- **API Docs**: https://norxynorzy-shl-recommender.hf.space/docs
# Contact Me

- [LinkedIn](https://www.linkedin.com/in/ajay-pentakoti-840b52324/)  
- [Gmail](mailto:ajay.pentakoti@gmail.com)



## System Architecture

```
Data Pipeline:
┌─────────────────┐
│  SHL Website    │ → Web Scraper
└─────────────────┘
         ↓
┌─────────────────────────────────┐
│  Product Catalog (377+ items)   │
│  - Titles, Descriptions         │
│  - Test Types, Job Levels       │
│  - URLs, Metadata               │
└─────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│ Embedding Generation                  │
│ - Sentence Transformers (all-MiniLM) │
│ - Normalize embeddings                │
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────┐
│  Vector Store (PyTorch Tensors)  │
│  - Efficient similarity search    │
│  - Cosine similarity metrics      │
└──────────────────────────────────┘
         ↓
┌──────────────────────────────────┐
│ Recommendation Engine             │
│ - Query understanding             │
│ - Skill domain detection          │
│ - Balanced recommendations        │
└──────────────────────────────────┘
         ↓
┌──────────────────────────────────┐
│ API & Web Interface               │
│ - FastAPI backend                 │
│ - Modern web frontend             │
└──────────────────────────────────┘
```

## Key Components

### 1. Web Scraper (`Scraper/scraper.py`)
- **Purpose**: Crawls SHL product catalog to build comprehensive assessment database
- **Coverage**: Scrapes 50+ pages to ensure ≥377 individual test solutions
- **Data Extracted**:
  - Assessment name and URL
  - Detailed description
  - Test type (K=Knowledge, P=Personality, S=Simulations, A=Ability)
  - Job levels (entry, mid, senior, etc.)
  - Languages supported
  - Duration and adaptive support flags
  - Remote testing availability
- **Rate Limiting**: 1-2 second delays to respect server load

### 2. Embedding Generation (`Embeddings/Embed.py`)
- **Model**: Sentence-Transformers (all-MiniLM-L6-v2)
  - Lightweight (22M parameters)
  - Fast inference
  - Strong semantic understanding
- **Text Representation**:
  - Weighted combination of name (2x), description, test type, job levels
  - Normalized L2 embeddings for cosine similarity
- **Storage**: PyTorch tensors for efficient retrieval

### 3. Recommendation Engine
- **Query Processing**:
  - Skill domain detection (technical vs. soft skills)
  - Keyword extraction and augmentation
  - URL content extraction if needed
- **Balanced Recommendations**:
  - Detects multi-domain queries (e.g., "Java + teamwork")
  - Returns balanced mix across assessment types
  - Example: Java query returns mix of Knowledge & Skills (K) and Personality tests (P)
- **Scoring**:
  - Cosine similarity between query and assessment embeddings
  - Top-k retrieval with dynamic balancing

### 4. API Endpoints (`api/app.py`)

#### Health Check
```
GET /health
Response: {"status": "healthy", "items": 377}
```

#### Recommendations
```
POST /recommend
Request: {"query": "Java developer with collaboration skills", "top_k": 10}
Response: {
    "recommended_assessments": [
        {
            "name": "Python (New)",
            "url": "https://www.shl.com/...",
            "description": "Multi-choice test...",
            "score": 0.892,
            "test_type": "K",
            "job_levels": "Entry, Mid",
            "adaptive_support": "No",
            "remote_testing": "Yes"
        },
        ...
    ]
}
```

### 5. Web Frontend (`web/index.html`)
- Modern, responsive design
- Real-time recommendations
- Visual indicators for assessment types
- Direct links to SHL catalog
- Copy-paste friendly interfaces

## Evaluation Metrics

### Mean Recall@K
The system is evaluated using Mean Recall@K metric across test queries:

$$\text{Recall@K} = \frac{\text{# relevant items in top K}}{\text{Total # relevant items}}$$

$$\text{Mean Recall@K} = \frac{1}{N}\sum_{i=1}^{N}\text{Recall@K}_i$$

Where N is total test queries.

### Performance Optimization Iterations

**Iteration 1: Basic Embedding Search**
- Simple semantic search with single embedding
- Mean Recall@10: ~0.45

**Iteration 2: Text Augmentation**
- Weight important fields (name, test_type, job_levels)
- Add keyword repetition in embedding text
- Mean Recall@10: ~0.62

**Iteration 3: Skill Domain Detection**
- Extract technical and soft skills from queries
- Augment query with relevant keywords
- Mean Recall@10: ~0.71

**Iteration 4: Balanced Recommendations**
- Detect multi-domain requirements
- Split recommendations by assessment type
- Ensures coverage of both hard and soft skills
- Mean Recall@10: ~0.78

## Technology Stack

- **Backend**: FastAPI, Python 3.9+
- **ML/NLP**: Sentence-Transformers, PyTorch, scikit-learn
- **Data Processing**: pandas, numpy
- **Web Scraping**: BeautifulSoup4, requests
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Uvicorn

## Setup Instructions

### Prerequisites
- Python 3.9+
- pip or conda

### Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Scrape SHL catalog** (if not already done):
```bash
python Scraper/scraper.py
```
This creates `api/final_catalog.json` with all assessments.

3. **Generate embeddings**:
```bash
python Embeddings/Embed.py
```
This creates `api/embeddings.pt` for fast retrieval.

4. **Run API server**:
```bash
python api/app.py
```
Server starts at `http://localhost:8000`

5. **Access web interface**:
Open browser to `http://localhost:8000`

## Running Evaluation

### On Training Set
```bash
python eval/evaluation.py
```
Outputs:
- Individual query recall scores
- Mean Recall@10 and Recall@5 across all queries

### Generate Test Predictions
```bash
python eval/generate_predictions.py
```
Creates `eval/submission.csv` in required format.

## Example Queries

1. **Technical + Soft Skills**
   - Query: "Java developer who can collaborate with external teams"
   - Expected: Mix of programming tests (K) + personality tests (P)

2. **Senior Leadership Role**
   - Query: "Senior manager with Python and R skills"
   - Expected: Leadership/management simulations (S) + technical assessments

3. **Entry Level Developer**
   - Query: "Entry level JavaScript developer"
   - Expected: Entry-level technical assessments (K)



## Future Improvements

1. **Hybrid Retrieval**:
   - Add BM25 keyword matching + semantic search ensemble
   - Improves recall on technical queries

2. **LLM-based Ranking**:
   - Use Gemini API to re-rank top-k results
   - Better relevance scoring for complex queries

3. **Caching & CDN**:
   - Cache embedding computations
   - Distribute across regions

4. **User Feedback Loop**:
   - Track query relevance feedback
   - Fine-tune embeddings based on feedback

**Last Updated**: December 2025

