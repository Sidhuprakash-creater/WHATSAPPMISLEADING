# 🛡️ MisLEADING — Complete Technical Reference

> Real-time, explainable AI platform that detects misinformation across text, URLs, images, and video — with deep support for Indian regional languages (Hindi, Odia, Hinglish).

---

## 📁 Project Structure

```
WHATSAPPMISLEADING/
├── backend/                    ← FastAPI Python Server
│   ├── main.py                 ← App factory + router registration
│   ├── config.py               ← Environment variable loader
│   ├── requirements.txt        ← Python dependencies
│   ├── misleading.db           ← SQLite database (dev)
│   │
│   ├── ai_wrapper/             ← 🧠 Core Intelligence Layer
│   │   ├── wrapper.py          ← Master orchestrator (run_full_analysis)
│   │   ├── llm_explainer.py    ← Groq/LLM deep reasoning module
│   │   ├── scoring.py          ← Weighted risk score engine
│   │   └── semantic_logic.py   ← FAISS vector memory (dedup)
│   │
│   ├── analyzers/              ← 🔍 Specialized Signal Analyzers
│   │   ├── text_analyzer.py    ← ML Tier-1 fast classification
│   │   ├── indic_analyzer.py   ← Hindi/Odia/Hinglish safe-pass regex
│   │   ├── url_analyzer.py     ← GSB + VirusTotal + WHOIS
│   │   ├── image_analyzer.py   ← Claude Vision + Sightengine
│   │   ├── fact_checker.py     ← Sentence-BERT + FAISS fact DB
│   │   ├── claim_extractor.py  ← Claim NLP extraction
│   │   ├── web_search_engine.py← Online claim verification
│   │   ├── language_detector.py← langdetect + spaCy ID
│   │   └── video_analyzer.py   ← Frame extraction → image pipeline
│   │
│   ├── api/v1/                 ← REST API Endpoints
│   │   ├── analyze.py          ← POST /analyze (main endpoint)
│   │   ├── auth.py             ← JWT login/register
│   │   ├── history.py          ← GET user scan history
│   │   ├── stats.py            ← GET daily dashboard stats
│   │   └── language.py         ← GET language detection test
│   │
│   ├── db/
│   │   ├── database.py         ← SQLAlchemy async engine setup
│   │   └── models.py           ← AnalysisRecord + DailyStat tables
│   │
│   ├── ml/
│   │   ├── model.pkl           ← Trained scikit-learn classifier
│   │   ├── train_local_llm.py  ← Knowledge distillation trainer
│   │   └── dataset_prep.py     ← Training data preparation
│   │
│   └── models/
│       └── custom_lang_id.joblib ← Custom language ID model
│
├── mobile/                     ← Flutter Android/iOS App
│   └── lib/
│       ├── main.dart           ← App entry + Firebase init
│       ├── models/             ← Data models (AnalysisResult, etc.)
│       ├── providers/          ← State management (Provider)
│       ├── screens/            ← UI screens (Home, QR, History)
│       ├── services/           ← api_service.dart (HTTP layer)
│       └── widgets/            ← verdict_card.dart, etc.
│
├── web/                        ← Next.js 14 Dashboard (WIP)
├── details.md                  ← This document
├── HOW_IT_WORKS.md             ← Team explanation (Hindi/English)
└── README.md                   ← Quick start guide
```

---

## 🛠️ Technology Stack

### 🔹 Backend

| Component | Technology | Version | Purpose |
|:---|:---|:---|:---|
| **Web Framework** | FastAPI | 0.115.0 | Async REST API + WebSocket server |
| **ASGI Server** | Uvicorn | 0.30.0 | High-performance async execution |
| **ORM** | SQLAlchemy | 2.0.35 | Database abstraction layer |
| **Async DB Driver** | aiosqlite | 0.20.0 | Non-blocking SQLite I/O |
| **Cache** | Redis | 5.1.0 | Sub-millisecond result caching |
| **Auth** | python-jose + passlib | 3.3.0 | JWT tokens + bcrypt hashing |
| **Rate Limiting** | SlowAPI | 0.1.9 | Anti-abuse protection |
| **HTTP Client** | httpx | 0.27.0 | Async external API calls |
| **Real-Time** | websockets | 13.0 | Live analysis status streaming |
| **Migrations** | Alembic | 1.13.0 | DB schema versioning |

### 🔹 AI & ML Libraries

| Library | Version | Role |
|:---|:---|:---|
| **scikit-learn** | 1.5.0 | TF-IDF + Logistic Regression classifier |
| **joblib** | 1.4.0 | ML model serialization (`.pkl`) |
| **groq** | 0.25.0 | Groq API SDK for cloud LLM inference |
| **sentence-transformers** | latest | `all-MiniLM-L6-v2` sentence embeddings |
| **faiss-cpu** | latest | Vector similarity search for fact-checking |
| **spaCy** | 3.7.0 | NLP, tokenization, entity extraction |
| **langdetect** | 1.0.9 | Statistical language identification |
| **pandas** | 2.2.0 | Dataset preprocessing |

### 🔹 Mobile (Flutter)

| Package | Version | Role |
|:---|:---|:---|
| **Flutter SDK** | Dart ^3.10.1 | Cross-platform UI framework |
| **provider** | ^6.1.5 | Reactive state management |
| **http** | ^1.6.0 | REST API communication |
| **firebase_core** | ^3.12.1 | Firebase initialization |
| **cloud_firestore** | ^5.6.5 | Cross-device scan history sync |
| **firebase_auth** | ^5.5.1 | User authentication |
| **mobile_scanner** | ^5.2.2 | QR code URL scanning |
| **image_picker** | ^1.2.1 | Image/video input |
| **qr_flutter** | ^4.1.0 | Share-as-QR output |
| **url_launcher** | ^6.3.2 | Open verified source links |

---

## 🔑 API Keys & Environment Configuration

All sensitive keys go in `backend/.env`. Copy from `backend/.env.example`.

```bash
# ─── AI Services ──────────────────────────────────────────────────────────
# Anthropic Claude (used for image analysis / Claude Vision)
ANTHROPIC_API_KEY=sk-ant-xxxxx...

# Groq Platform (used for LLM reasoning - Llama 3.1 8B Instant)
# Get yours FREE at: https://console.groq.com
GROQ_API_KEY=gsk_xxxxx...

# ─── URL Security APIs ────────────────────────────────────────────────────
# Google Safe Browsing — detects phishing/malware URLs
# Get at: https://developers.google.com/safe-browsing
GOOGLE_SAFE_BROWSING_KEY=AIzaSy...

# VirusTotal — community-based file & URL scanning
# Get at: https://www.virustotal.com/gui/my-apikey
VIRUSTOTAL_API_KEY=xxxx...

# ─── Image Moderation ────────────────────────────────────────────────────
# Sightengine — NSFW, deepfake, AI-generation detection
# Get at: https://sightengine.com/
SIGHTENGINE_API_USER=your-user
SIGHTENGINE_API_SECRET=your-secret

# ─── Database ─────────────────────────────────────────────────────────────
# Default uses SQLite in dev. Switch to PostgreSQL for production:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/misleading

# ─── Cache ────────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ─── Auth ────────────────────────────────────────────────────────────────
JWT_SECRET=change-this-to-a-very-long-random-string
JWT_EXPIRE_MINUTES=60

# ─── App ─────────────────────────────────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=INFO
```

> **Note:** `GROQ_API_KEY` is the primary key for all LLM reasoning. `ANTHROPIC_API_KEY` is used only for Claude Vision image analysis. Both can operate independently.

---

## 🧠 AI Model Architecture (Deep Dive)

The system uses a **3-tier AI pipeline** — each tier is faster but less accurate than the next. The fastest possible path is always taken first.

```
INPUT TEXT/URL/IMAGE/VIDEO
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 0 — INSTANT MEMORY (0ms)                                      │
│  ┌───────────────────┐    ┌─────────────────────────────────────┐   │
│  │   Persistent Cache │    │  FAISS Semantic Vector Memory       │   │
│  │  (JSON on disk)   │    │  all-MiniLM-L6-v2 embeddings        │   │
│  │  Exact hash match  │    │  L2 distance similarity search      │   │
│  └───────────────────┘    └─────────────────────────────────────┘   │
│   ↓ CACHE HIT → Return instantly                                     │
│   ↓ SEMANTIC MATCH → Return instantly                                │
└─────────────────────────────────────────────────────────────────────┘
         │ MISS — go to next tier
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 1 — FAST BRAIN: ML Model + Indic Regex (< 50ms)              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Indic Regex Engine (Priority 1 — 0ms)                       │   │
│  │  50+ regex patterns for Odia/Hindi/Hinglish safe phrases     │   │
│  │  If matched → score -= 35, return SAFE immediately           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  scikit-learn Classifier (TF-IDF + Logistic Regression)      │   │
│  │  File: ml/model.pkl (trained on Indian misinformation data)  │   │
│  │  Labels: fake | misleading | scam | normal | promotional     │   │
│  │  Output: { label, probability, confidence 0-100 }            │   │
│  │  If ML says SAFE (≥70% confidence) → FAST PASS, skip LLM    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         │ SUSPICIOUS — escalate to Deep Brain
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 2 — DEEP BRAIN: LLM + RICH EXPLAINER (2-5 seconds)            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Model: llama-3.1-8b-instant (via Groq Cloud)                │   │
│  │  Prompt: Output STUCTURED JSON with explanations & patterns   │   │
│  │  Output:                                                     │   │
│  │    → why_fake: list[str] (Bullet points for mobile UI)       │   │
│  │    → entities: list[dict] (Enriched person/org data)         │   │
│  │    → claim_vs_reality: list[dict] (Comparison rows)          │   │
│  │    → safe_to_forward: boolean (Final user guidance)          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  ENTITY ENRICHMENT (Parallel with LLM)                       │   │
│  │  → Local DB: 15,000+ Indian Public Figures (Politicians)     │   │
│  │  → Wikipedia API: Asynchronous summary enrichment             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  WEB SEARCH SYNTHESIS (Final Verification)                   │   │
│  │  → Search: DuckDuckGo/Tavily for primary claim               │   │
│  │  → Synthesis: LLM converts snippets into REAL vs FAKE text   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 3 — SCORING ENGINE (scoring.py)                               │
│   Aggregates all signals into a single 0-100 Risk Score             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚖️ The Scoring Engine — Full Weights Matrix

`backend/ai_wrapper/scoring.py` applies a **weighted evidence scoring** model. All applicable signals are **additive** (bonus for bad signals, negative for good signals), then clamped to `[0, 100]`.

| Signal | Score | Trigger |
|:---|:---:|:---|
| **ML → FAKE** (>80% confidence) | +40 | Model has high certainty |
| **ML → FAKE** (60–80% confidence) | +25 | Model has moderate certainty |
| **ML → MISLEADING** | +20 | Flagged as misleading at any confidence |
| **URL: Malware** (Google Safe Browsing) | +35 | Active phishing/malware threat |
| **URL: VirusTotal** (5+ engines) | +25 | Community-confirmed bad URL |
| **URL: Domain Too Young** (<7 days) | +15 | Scammer hallmark |
| **URL: Suspicious Pattern** | +8 | Keyword/structure heuristic |
| **Image: AI-Generated** (>70%) | +20 | Sightengine deepfake detection |
| **Image: NSFW** | +15 | Explicit content detected |
| **LLM: Emotional Manipulation** | +10 | Fear/urgency language patterns |
| **LLM: No Source Cited** | +10 | Unsourced viral claim |
| **LLM: Viral Pressure** | +8 | "Forward to 10 people" type |
| **LLM: Conspiracy Framing** | +10 | Anti-establishment narratives |
| **LLM: Impossible / Unverifiable** | +40 | Physically impossible claims |
| **LLM: High/Extreme Severity** | +45 | Threats to national leaders/safety |
| **Web: No Evidence Found** | +20 | Penalty for unverifiable public claims |
| **Public Figure + Unverified** | →88 | Override: minimum score forced to 88 |
| **Established Domain** (>2 years) | -10 | Trust bonus for old domains |
| **Corroborated by Sources** | -15 | Multiple credible sources confirm |
| **Indic Safe Context** (regex match) | -35 | Harmless regional phrase detected |

### Verdict Thresholds

```
Score 0  ──────── 30 ──────── 60 ──────── 100
  │                │            │            │
  └── 🟢 Low Risk  └─ 🟠 Medium  └─ 🔴 High  ┘
       (Safe)         (Misleading)   (Fake/Dangerous)
```

---

## 🔄 Full System Data Flow

```mermaid
flowchart TD
    A[👤 User / Mobile App] -->|POST /api/v1/analyze| B[FastAPI Backend]

    B --> C{Persistent Cache Hit?}
    C -->|Yes ✅| Z[Return Cached Result]
    C -->|No| D{Semantic FAISS Memory Hit?}
    D -->|Similar found ✅| Z
    D -->|No| E[Run Parallel Analyzers]

    E --> F[Indic Regex Engine\n0ms - Odia/Hindi/Hinglish]
    E --> G[ML Classifier\nTF-IDF + Logistic Regression]
    E --> H[URL Analyzer\nGSB + VirusTotal + WHOIS]
    E --> I[Image Analyzer\nClaude Vision + Sightengine]
    E --> J[Video Analyzer\nFrame Extraction → Image]

    F -->|Safe Pattern| K[Score -35 → FAST PASS]
    G -->|≥70% Safe| K
    G -->|Suspicious| L[LLM Explainer\nGroq: llama-3.1-8b-instant]
    L -->|high/extreme| M[Fact Checker\nFAISS DB + Web Search]

    K --> N[Scoring Engine\nWeighted 0-100 Matrix]
    H --> N
    I --> N
    J --> N
    L --> N
    M --> N

    N -->|Score ≥ 60| O[🔴 High Risk Verdict]
    N -->|Score 30-59| P[🟠 Medium Risk Verdict]
    N -->|Score 0-29| Q[🟢 Low Risk Verdict]

    O --> R[Save to SQLite DB\nWritten to Redis Cache\nSelf-learn to FAISS Memory]
    P --> R
    Q --> R

    R --> S[📱 Flutter App Shows Verdict Card]
```

---

## 🤖 ML Model Deep Dive

### Training Pipeline (`ml/train_local_llm.py`, `ml/dataset_prep.py`)

| Step | Detail |
|:---|:---|
| **Input** | Indian WhatsApp misinformation dataset (CSV) |
| **Preprocessing** | Lowercase + remove URLs/mentions + Unicode normalization (NFKC) |
| **Vectorization** | `TfidfVectorizer` — converts text to statistical word-frequency vectors |
| **Classifier** | `LogisticRegression` (or similar sklearn model) |
| **Labels** | `fake`, `misleading`, `scam`, `normal`, `spam`, `promotional` |
| **Output** | Pickled model saved as `ml/model.pkl` |
| **Load** | On server startup, loaded once into `app.state.ml_model` |

### How the Model is Used

```python
# Pseudo-code of text_analyzer.py flow:
prediction = ml_model.predict([clean_text])[0]       # → "fake"
probabilities = ml_model.predict_proba([clean_text])  # → [0.12, 0.88, ...]
confidence = int(probabilities[pred_idx] * 100)       # → 88%

# Gateway logic:
if confidence >= 70 and label in ("normal", "safe"):
    return FAST_PASS  # Skip LLM
else:
    return ESCALATE_TO_LLM
```

---

## 🤯 LLM Model Deep Dive

### Model: `llama-3.1-8b-instant` via Groq Cloud

| Parameter | Value |
|:---|:---|
| **Provider** | [Groq](https://groq.com/) (uses custom LPU hardware) |
| **Model** | `llama-3.1-8b-instant` |
| **Temperature** | `0.1` (very low = consistent, fact-like output) |
| **Max Tokens** | `600` (strict to prevent overthinking) |
| **Response Format** | `json_object` (guaranteed parseable JSON) |
| **Timeout** | `5 seconds` (async `wait_for` — falls back to ML result) |
| **API Key** | `GROQ_API_KEY` in `.env` |

### System Prompt Design

The LLM is given a strict persona as **"MisLEADING AI"** with these instructions:
1. Analyze for Indian regional misinformation patterns.
2. Return **only valid JSON** — no prose, no markdown.
3. If a public figure + death/arrest rumor is detected → set `severity: extreme`.
4. If harmless regional daily phrases (`hei gala`, `ho gaya`) found → set `SAFE`.

### LLM JSON Output Schema

```json
{
  "patterns_found": [
    {
      "type": "emotional_manipulation",
      "evidence": "Uses urgent language: 'Share before government deletes'"
    }
  ],
  "severity": "high",
  "primary_claim": "Government is providing free laptops",
  "is_public_figure": false,
  "llm_confidence_adjustment": 30,
  "explanation": "This message uses classic scarcity tactics to provoke urgency..."
}
```

### LLM Escalation Trigger

The LLM is **not called for every message** — only when:
- ML classifier returns `fake`, `scam`, `misleading`, `toxic`, or `promotional`
- No ML model is loaded (fallback)
- ML confidence is below 70%

This ensures the LLM is invoked intelligently, reducing latency for safe messages.

---

## 🌐 Semantic Memory & Self-Learning

### FAISS Vector Memory (`ai_wrapper/semantic_logic.py`)

On every completed analysis:
1. The input text is encoded into a **384-dimension vector** using `all-MiniLM-L6-v2`.
2. The vector + result is stored in a **FAISS IndexFlatL2** index in memory.
3. On the next request, if a new input is semantically within **distance < threshold**, the cached result is returned **instantly** without re-running the pipeline.

This is the system's "**Instant Brain**" — it learns from every scan.

### Persistent Disk Cache

A JSON file (`data/analysis_cache.json`) saves **exact** input-to-result mappings that survive server restarts. On boot, these are also bootstrapped into the FAISS memory for semantic coverage.

---

## 🗄️ Database Schema

### Table: `analysis_history`

| Column | Type | Description |
|:---|:---|:---|
| `id` | String(36) | UUID primary key |
| `content_type` | String(20) | `text`, `url`, `image`, `video` |
| `content` | String | Raw input text/URL/file ref |
| `verdict` | String(50) | `High Risk` / `Medium Risk` / `Low Risk` |
| `risk_score` | Integer | Final computed score (0–100) |
| `confidence` | Integer | Model confidence (0–100) |
| `reasons` | JSON | List of user-facing explanation strings |
| `raw_signals` | JSON | Full signals dict for debugging |
| `processing_ms` | Integer | Total pipeline execution time |
| `client_ip` | String(50) | For rate limiting / audit |
| `created_at` | DateTime (TZ) | UTC timestamp |

### Table: `daily_stats`

| Column | Type | Description |
|:---|:---|:---|
| `id` | Integer | Auto-increment PK |
| `date` | String(10) | `YYYY-MM-DD` (unique) |
| `total_scans` | Integer | Total analyses that day |
| `fake_detected` | Integer | Count of High Risk results |
| `avg_processing_time` | Float | Average ms per analysis |
| `created_at` | DateTime (TZ) | Row creation timestamp |

---

## 🔌 API Endpoints

| Method | Path | Description |
|:---|:---|:---|
| `GET` | `/` | Health check + ML model status |
| `GET` | `/health` | Redis + ML status check |
| `POST` | `/api/v1/analyze` | **Main** — run full analysis pipeline |
| `POST` | `/api/v1/auth/register` | Create new user account |
| `POST` | `/api/v1/auth/login` | Login, returns JWT token |
| `GET` | `/api/v1/history` | Retrieve user's scan history |
| `GET` | `/api/v1/stats` | Dashboard statistics |
| `GET` | `/api/v1/language` | Language detection test endpoint |
| `WS` | `/ws/analyze` | WebSocket streaming analysis |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/redoc` | ReDoc API documentation |

---

## 🚀 Quick Start

```bash
# 1. Clone & setup backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Configure API Keys
copy .env.example .env
# Edit .env and fill in your GROQ_API_KEY etc.

# 3. Start server
uvicorn main:app --reload --port 8000

# 4. Open API Docs
# http://localhost:8000/docs

# 5. Mobile App
cd mobile
flutter pub get
flutter run
```

---

*📅 Last Updated: April 2026 — MisLEADING Development Team*
