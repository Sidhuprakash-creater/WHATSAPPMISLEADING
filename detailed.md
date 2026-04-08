# MisLEADING - Technical Documentation

> Multi-Modal AI Misinformation Detection Platform

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Frontend Architecture](#frontend-architecture)
3. [Backend Architecture](#backend-architecture)
4. [AI Models & Pipeline](#ai-models--pipeline)
5. [System Architecture](#system-architecture)
6. [Development Workflow](#development-workflow)
7. [Configuration](#configuration)
8. [Lessons Learned & Future Improvements](#lessons-learned--future-improvements)

- [**Testing & Deployment Guide**](file:///d:/WHATSAPPMISLEADING/testing_guide.md): Step-by-step verification commands.
- [**Architecture Diagram**](file:///d:/WHATSAPPMISLEADING/detailed.md): System technical overview.

---

## 🛠️ Tech Stack & Design

### Backend

| Technology | Purpose | Rationale |
|:-----------|:--------|:-----------|
| **FastAPI** | Web framework | High-performance async framework, built-in OpenAPI docs, native support for async/await |
| **Python 3.11+** | Language | Strong AI/ML ecosystem (PyTorch, scikit-learn, transformers) |
| **SQLAlchemy 2.0** | ORM | Async support with aiosqlite (dev) / asyncpg (prod), type-safe queries |
| **SQLite** (dev) / **PostgreSQL** (prod) | Database | SQLite for local dev; PostgreSQL for production with proper scaling |
| **Redis** | Caching | Sub-3-second response time target, cache analysis results |
| **Groq API** | Primary LLM | Fast inference with `llama-3.3-70b-versatile` for primary verdict |
| **Gemini Vision API** | Image analysis | Multimodal AI for deepfake/AI-generated image detection |
| **Google Safe Browsing API** | URL security | Real-time threat detection for phishing/malware URLs |
| **VirusTotal API** | URL security | Multi-engine malware scanning |
| **scikit-learn** | ML classifier | Fast "Fast Brain" text classification (currently bypassed in v3) |
| **FAISS + sentence-transformers** | Semantic search | Local fact-check database for known debunked myths |
| **DuckDuckGo Search** | Web fact-check | Online evidence gathering for unverified claims |

### Frontend - Mobile (Flutter)

| Technology | Purpose |
|:-----------|:--------|
| **Flutter 3.x** | Cross-platform mobile UI |
| **Provider** | State management |
| **Firebase Auth** | Anonymous authentication |
| **Cloud Firestore** | Chat/message storage |
| **image_picker** | Camera/gallery access |
| **mobile_scanner** | QR code scanning |

### Frontend - Web (Next.js)

| Technology | Purpose |
|:-----------|:--------|
| **Next.js 14** | React framework (partially implemented) |
| **Tailwind CSS** | Styling |

---

## Frontend Architecture

### Mobile App (Flutter)

```
lib/
├── main.dart                    # Entry point, Firebase init
├── models/
│   └── message.dart             # Message & ScanResult models
├── providers/
│   ├── chat_provider.dart       # Chat state management
│   └── user_provider.dart       # User state management
├── screens/
│   ├── home_screen.dart         # Main WhatsApp-style UI
│   ├── chat_list_screen.dart    # Chat list
│   ├── chat_detail_screen.dart  # Individual chat
│   ├── profile_screen.dart      # User profile
│   ├── qr_scanner_screen.dart  # QR code scanner
│   └── add_friend_screen.dart  # Add contacts
├── services/
│   └── api_service.dart         # Backend API communication
└── widgets/
    ├── bottom_input_bar.dart    # Message input
    ├── message_bubble.dart      # Chat bubbles
    └── verdict_card.dart        # Analysis result display
```

#### State Management
- **Provider** pattern for reactive state
- `ChatProvider` manages chat messages and analysis results
- `UserProvider` manages user profile and online status

#### API Communication
- Backend URL configured in `api_service.dart:10`
- Default: `http://40.0.3.134:8000/api/v1` (local network IP)
- Supports base64-encoded file uploads for images/APKs

#### Key Flows
1. **Text Analysis Flow**: User enters text → API call → Display verdict card
2. **Image Analysis Flow**: Camera/gallery → Base64 encode → API call → Display result
3. **URL Analysis Flow**: Paste URL → Auto-extraction → Security scan → Verdict

---

## Backend Architecture

### Directory Structure

```
backend/
├── main.py                      # FastAPI app factory, lifespan events
├── config.py                    # Pydantic Settings (.env loader)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (SECRETS)
├── .env.example                # Template for env vars
├── api/
│   ├── __init__.py
│   ├── websocket.py            # Real-time progress streaming
│   └── v1/
│       ├── analyze.py           # POST /api/v1/analyze (main endpoint)
│       ├── auth.py             # JWT authentication
│       ├── history.py          # Analysis history
│       ├── stats.py            # Daily statistics
│       └── language.py         # Language detection
├── analyzers/
│   ├── text_analyzer.py        # ML classifier (bypassed in v3)
│   ├── url_analyzer.py         # Google Safe Browsing + VirusTotal
│   ├── image_analyzer.py       # Gemini Vision for deepfakes
│   ├── video_analyzer.py       # Frame extraction + image analysis
│   ├── apk_analyzer.py         # APK/document security
│   ├── fact_checker.py         # FAISS + sentence-transformers
│   ├── claim_extractor.py      # Extract claims from text
│   ├── web_search_engine.py    # DuckDuckGo fact-check
│   ├── indic_analyzer.py       # Hindi/Odia regional patterns
│   └── language_detector.py    # Language identification
├── ai_wrapper/
│   ├── wrapper.py              # Main orchestrator (v3 Groq-Primary)
│   ├── llm_explainer.py        # Groq LLM integration
│   ├── semantic_logic.py      # Semantic memory (FAISS)
│   └── scoring.py              # Score computation
├── db/
│   ├── database.py             # SQLAlchemy async engine
│   └── models.py               # ORM models (AnalysisRecord, DailyStat)
└── data/
    ├── politicians_db.json     # Entity database for public figures
    └── analysis_cache.json    # Persistent analysis cache
```

### API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/` | GET | Root health check |
| `/health` | GET | Detailed health status |
| `/api/v1/analyze` | POST | Main analysis (text/URL/image/video) |
| `/api/v1/clear_cache` | POST | Purge analysis cache |
| `/api/v1/auth/register` | POST | User registration |
| `/api/v1/auth/login` | POST | JWT login |
| `/api/v1/history` | GET | Paginated analysis history |
| `/api/v1/stats` | GET | Daily statistics |
| `/api/v1/language/detect` | POST | Language detection |
| `/ws/analysis/{id}` | WebSocket | Real-time progress streaming |

### Request/Response Format

#### Analyze Request
```json
{
  "content_type": "text|url|image|video|document",
  "text": "string (for text/url)",
  "file_url": "string (for image/video)",
  "session_id": "optional"
}
```

#### Analyze Response
```json
{
  "id": "uuid",
  "verdict": "High Risk|Medium Risk|Low Risk",
  "confidence": 0-100,
  "risk_score": 0-100,
  "reasons": ["reason 1", "reason 2"],
  "explanation": {
    "summary": "forensic report text",
    "primary_claim": "core assertion",
    "why_fake": ["reason 1", "reason 2"],
    "entities": [...],
    "claim_vs_reality": [...],
    "patterns_found": [...],
    "verified_sources": [...],
    "safe_to_forward": boolean,
    "url_security": {...}
  },
  "signals": {
    "llm": {...},
    "url": {...},
    "media": {...}
  },
  "processing_ms": 1500
}
```

### Database Schema

#### AnalysisRecord
| Column | Type | Description |
|:-------|:-----|:------------|
| id | String(36) | UUID primary key |
| content_type | String | text, url, image, video |
| content | String | Original content (truncated) |
| verdict | String | High/Medium/Low Risk |
| risk_score | Integer | 0-100 |
| confidence | Integer | 0-100 |
| reasons | JSON | List of reason strings |
| raw_signals | JSON | Full AI wrapper output |
| processing_ms | Integer | Processing time |
| client_ip | String | Client IP address |
| created_at | DateTime | Timestamp |

#### DailyStat
| Column | Type | Description |
|:-------|:-----|:------------|
| id | Integer | Auto-increment |
| date | String(10) | YYYY-MM-DD |
| total_scans | Integer | Total analyses |
| fake_detected | Integer | High-risk detections |
| avg_processing_time | Float | Average ms |

## 🛡️ Real-Time Safety Guard (NEW!)
The system now includes an automatic safety layer in both the Mobile App and Backend.

**Key Features:**
- **Auto-Delete**: Restricted words are instantly removed from the UI keyboard bar.
- **Warning System**: Users receive a popup explaining the restriction.
- **Backend Sanitization**: All text is re-verified at `is_safe_text` level before analysis.

---

## 🧪 Testing & Verification
Refer to [Testing Guide](file:///d:/WHATSAPPMISLEADING/testing_guide.md) for full cURL examples.

### Core Testing Command:
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"content_type": "text", "text": "Drink bleach to cure disease"}'
```

---

## AI Models & Pipeline

### Pipeline Architecture (v3 - Groq-Primary)

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Cache Check (Redis + Semantic Memory)            │
│  - SHA256 hash lookup                                        │
│  - FAISS semantic similarity search                         │
└─────────────────────────────────────────────────────────────┘
    │ Cache Miss
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Content Routing                                    │
│  - Text → Language Detection                                │
│  - URL → Extract & Security Scan                           │
│  - Image/Video → Media Analysis                            │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Parallel Analyzers                                │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐   │
│  │ URL Analyzer│ │Media Analyzer│ │ Fact Check Engine│   │
│  │ (GSB + VT)  │ │(Gemini Vision│ │ (FAISS + Web)    │   │
│  └─────────────┘ └──────────────┘ └───────────────────┘   │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Groq LLM Primary Verdict                          │
│  Model: llama-3.3-70b-versatile                             │
│  Input: text + URL results + fact-check evidence           │
│  Output: Structured JSON verdict                           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Score Computation                                  │
│  - Severity mapping: extreme→92, high→72, medium→42        │
│  - URL penalties: GSB threat +50, VT malicious +40        │
│  - Media penalties: NSFW +85, AI-generated >80 +score     │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Response Assembly                                  │
│  - Verdict: Low Risk (<30), Medium (30-59), High (60+)    │
│  - Rich explanation building                               │
│  - Cache storage                                            │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Final Response
```

### Model Details

#### 1. Groq LLM (Primary Verdict)
- **Model**: `llama-3.3-70b-versatile`
- **Purpose**: Main misinformation analysis engine
- **Training**: Pre-trained on diverse text corpus
- **Inference**:
  - System prompt defines forensic analysis guidelines
  - Language-specific instructions (Hindi, Odia, Hinglish, English)
  - Returns structured JSON with severity, entities, patterns
- **Integration**: Direct API call via `groq` Python library

#### 2. Gemini Vision (Image Analysis)
- **Model**: `gemini-2.0-flash`
- **Purpose**: Detect AI-generated images, deepfakes, NSFW content
- **Training**: Pre-trained multimodal model
- **Inference**:
  - Analyzes image bytes
  - Returns AI confidence (0-100), NSFW flag, manipulation signs
- **Integration**: `google.generativeai` Python library

#### 3. Google Safe Browsing (URL Security)
- **API Version**: v4
- **Threat Types**: MALWARE, SOCIAL_ENGINEERING, UNWANTED_SOFTWARE
- **Purpose**: Real-time URL threat detection

#### 4. VirusTotal (URL Security)
- **Purpose**: Multi-engine malware scanning
- **Scoring**: Malicious engine count determines risk

#### 5. FAISS Fact-Check Engine
- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Purpose**: Semantic search against curated debunked myths
- **Index**: FAISS L2 distance index on 10+ known facts
- **Threshold**: L2 distance < 1.2 = semantically similar claim found

#### 6. Web Search Fact-Check
- **Engine**: DuckDuckGo (`duckduckgo_search`)
- **Purpose**: Online evidence gathering
- **Timeout**: 7 seconds max
- **Filter**: Excludes mythological results (Mahabharata, etc.)

### Bypass Logic

#### Critical Keywords (Always Force Fresh Analysis)
```python
CRITICAL_BYPASS_WORDS = [
    "death", "dead", "murder", "kill", "maut", "mar gaya", "hatya",
    "scam", "prize", "lottery", "winner", "reward", "cash", "click",
    "arrested", "blast", "attack", "bomb", "rape", "riot",
]
```

#### Regional Safe Patterns (Instant Pass)
Fast regex patterns for Hindi/Odia safe content (greetings, regional verbs) that bypass deep analysis.

---

## System Architecture

### High-Level Data Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Flutter App    │     │   Next.js Web    │     │   Other Clients  │
│   (Mobile)       │     │   (Frontend)     │     │                  │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                       │                        │
         │     HTTPS/WSS         │                        │
         └───────────────────────┼────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │     FastAPI Backend    │
                    │    (Python/FastAPI)    │
                    └────────────┬───────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Redis Cache   │   │  SQLite/Postgres│   │   WebSocket    │
│   (Optional)    │   │   (History)     │   │   (Progress)   │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Groq API       │   │  Gemini Vision  │   │  URL Security  │
│   (LLM Verdict) │   │  (Image AI)     │   │  (GSB + VT)    │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Fact-Check Engine     │
                    │   (FAISS + Web Search) │
                    └────────────────────────┘
```

### Component Interactions

1. **User submits content** → Flutter sends to `/api/v1/analyze`
2. **Backend receives** → Checks Redis cache (instant return if hit)
3. **Cache miss** → Language detection + content routing
4. **Parallel execution**:
   - URL security scan (GSB + VirusTotal)
   - Media analysis (Gemini)
   - Claim extraction for fact-check
5. **Groq LLM receives** → Full context (text + URL results + fact-check)
6. **Score computation** → Combines all signals into risk score
7. **Response** → Verdict + rich explanation + sources
8. **Storage** → Save to SQLite + update daily stats + cache result

---

## Development Workflow

### Prerequisites

- Python 3.11+
- Node.js 18+ (for web)
- Flutter 3.x SDK
- Redis (optional, for caching)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
copy .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access API docs at http://localhost:8000/docs
```

### Mobile Setup

```bash
cd mobile

# Install dependencies
flutter pub get

# Run on device/emulator
flutter run
```

### Testing

```bash
# Backend tests
cd backend
python -m pytest  # If pytest is configured

# Quick test script
python test_images.py
python test_apk.py

# Clear cache during development
curl -X POST http://localhost:8000/api/v1/clear_cache
```

### Linting

```bash
# Python linting (ruff)
ruff check backend/

# Format
ruff format backend/
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `GROQ_API_KEY` | Yes | - | Groq API key for LLM (get from console.groq.com) |
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key (get from console.cloud.google.com) |
| `GOOGLE_SAFE_BROWSING_KEY` | No | - | Google Safe Browsing API key |
| `VIRUSTOTAL_API_KEY` | No | - | VirusTotal API key |
| `JWT_SECRET` | Yes | - | Secret key for JWT tokens |
| `JWT_EXPIRE_MINUTES` | No | 60 | Token expiration time |
| `DATABASE_URL` | No | sqlite+aiosqlite | Database connection string |
| `REDIS_URL` | No | redis://localhost:6379/0 | Redis connection URL |
| `ENVIRONMENT` | No | development | dev/prod |
| `LOG_LEVEL` | No | INFO | DEBUG/INFO/WARNING/ERROR |

### Sample `.env` File

```bash
# AI Keys (REQUIRED)
GROQ_API_KEY=gsk_your-key-here
GEMINI_API_KEY=AIzaSy your-key-here

# URL Security
GOOGLE_SAFE_BROWSING_KEY=AIzaSy your-key-here
VIRUSTOTAL_API_KEY=your-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./misleading.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/misleading

# Cache
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRE_MINUTES=60

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### API Keys Information

#### Getting API Keys

1. **Groq API Key**
   - Visit https://console.groq.com/
   - Create account → Generate API key
   - Free tier: 60K tokens/minute

2. **Gemini API Key**
   - Visit https://console.cloud.google.com/apis/credentials
   - Create project → Credentials → API Key
   - Enable "Gemini API" for your project

3. **Google Safe Browsing**
   - Visit https://developers.google.com/safe-browsing/
   - Get API key from Google Cloud Console

4. **VirusTotal**
   - Visit https://www.virustotal.com/
   - API key from account settings

#### Security Notes

> ⚠️ **IMPORTANT**: The `.env` file contains real API keys in this project. In production:
> - Never commit `.env` to version control
> - Use secrets management (HashiCorp Vault, AWS Secrets Manager)
> - Rotate API keys periodically
> - Restrict API key permissions to minimum required

---

## Lessons Learned & Future Improvements

### Key Insights

1. **Hybrid AI Architecture**
   - The "Fast Brain (ML) + Deep Brain (LLM)" concept proved valuable
   - In v3, ML model is locked - LLM handles all decisions for consistency

2. **Caching is Critical**
   - Target <3 second response requires aggressive caching
   - Redis + semantic FAISS memory reduces redundant API calls

3. **Multi-Language Support**
   - Hindi, Odia, Hinglish detection essential for Indian context
   - Language-specific prompts improve LLM accuracy

4. **Parallel Processing**
   - URL security scans run in parallel with content analysis
   - Async/await critical for performance

### Pain Points

1. **API Rate Limits**
   - Groq and VirusTotal have rate limits
   - Need better queue/backoff logic

2. **Local LLM (Ollama) Issues**
   - Initial plan included local Ollama for privacy
   - Local inference too slow for <3s target
   - Removed from v3 pipeline

3. **Mobile Network Instability**
   - 75-second timeout needed for slow connections
   - Base64 encoding increases payload size

### Future Improvements

1. **Model Improvements**
   - Fine-tune a dedicated misinformation detection model
   - Add support for more Indian languages (Tamil, Bengali, Marathi)
   - Implement custom trained image deepfake detector

2. **Architecture**
   - Switch to PostgreSQL for production
   - Add message queue (Celery/Redis Queue) for async processing
   - Implement WebSocket for real-time analysis progress

3. **Features**
   - Admin dashboard for analytics
   - Browser extension integration
   - WhatsApp Business API integration
   - Share analysis results as images

4. **Scaling**
   - Containerize with Docker
   - Kubernetes deployment
   - CDN for static assets
   - Load balancing multiple instances

5. **Security**
   - Implement rate limiting per user
   - Add request signing
   - Audit logging
   - Move secrets to vault

---

## Features Summary

### Implemented Features

| Feature | Status | Description |
|:--------|:-------|:------------|
| Text Analysis | ✅ | Groq LLM with multi-language support |
| URL Security | ✅ | Google Safe Browsing + VirusTotal |
| Image Analysis | ✅ | Gemini Vision for deepfakes/AI generation |
| Video Analysis | ✅ | Frame extraction + image analysis |
| APK Analysis | ✅ | Document security scanning |
| Fact-Check | ✅ | FAISS + Web search evidence |
| Multi-Language | ✅ | Hindi, Odia, Hinglish, English |
| WhatsApp UI | ✅ | Flutter mobile app |
| Real-time Progress | ✅ | WebSocket streaming |
| Caching | ✅ | Redis + persistent cache |
| History/Stats | ✅ | SQLite storage |

---

*Generated: 2026-04-07*
