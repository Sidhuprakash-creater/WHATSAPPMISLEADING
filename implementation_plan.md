# 🛡️ Multi-Modal AI Misinformation Detection System
## Complete Implementation Plan & How It Works

---

## 🧠 How The System Works

### The Core Idea
This is NOT a simple "fake or real" classifier. It's a **3-tier reasoning engine** that:
1. **Quickly scans** content using a trained ML model (< 50ms)
2. **Deeply analyzes** using an LLM for reasoning (Claude 3.5 Sonnet)
3. **Fuses all signals** through a weighted scoring engine to produce a final verdict with **human-readable explanations**

### The 3-Tier AI Architecture

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: FAST BRAIN (ML Model — always runs first)      │
│  ─────────────────────────────────────────────────────── │
│  • TF-IDF Vectorizer → Logistic Regression              │
│  • Trained on LIAR dataset (12,836 labeled statements)   │
│  • Converts text to numbers, finds "fake" word patterns  │
│  • Output: { label: 'fake', probability: 0.87 }          │
│  • Speed: < 50ms                                         │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 2: DEEP BRAIN (LLM — enriches the ML result)      │
│  ─────────────────────────────────────────────────────── │
│  • Claude 3.5 Sonnet via Anthropic API                   │
│  • Receives: raw text + ML model's prediction            │
│  • Detects things ML CANNOT:                             │
│    → Emotional manipulation (fear, urgency, guilt)       │
│    → Missing/unverifiable sources                        │
│    → Viral forwarding language ("share before deleted")   │
│    → Logical fallacies and impossible claims              │
│  • Output: patterns_found[] + explanation                │
│  • Speed: ~1.2 seconds                                   │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 3: AI WRAPPER (Orchestrator — the "Judge")         │
│  ─────────────────────────────────────────────────────── │
│  • Pure Python logic (no AI model)                       │
│  • Collects signals from ALL analyzers                   │
│  • Applies weighted scoring matrix (see below)           │
│  • Generates final verdict: High/Medium/Low Risk         │
│  • Produces confidence score: 0-100                      │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 How Scoring Works (The Weighted Matrix)

When the AI Wrapper receives signals, it assigns points:

| Signal | Points |
|:---|:---|
| ML Model → FAKE (>80% confidence) | +40 |
| ML Model → FAKE (60-80% confidence) | +25 |
| ML Model → MISLEADING | +20 |
| URL → MALWARE/PHISHING detected | +35 |
| URL → Domain age < 7 days | +15 |
| URL → VirusTotal flagged by 5+ engines | +25 |
| Image → AI-generated probability > 0.7 | +20 |
| LLM → Emotional manipulation detected | +10 |
| LLM → No credible source found | +10 |
| LLM → Viral pressure language found | +8 |
| Domain → Established (age > 2 years) | -10 |
| Multiple corroborating news sources | -15 |

### Verdict Thresholds

| Score Range | Verdict | Meaning |
|:---|:---|:---|
| 0 – 29 | 🟢 **Low Risk** | Likely safe, no significant signals |
| 30 – 59 | 🟡 **Medium Risk** | Some suspicious signals, verify manually |
| 60 – 100 | 🔴 **High Risk** | Strong indicators of misinformation |

---

## 🔄 Request Lifecycle (What Happens When You Submit Content)

```
User submits content (text/URL/image/video)
          │
          ▼
   [Input Router]  ── Detect content type (text? URL? image?)
          │
          ▼
   [Cache Check]  ── Redis lookup by SHA-256 hash
          │
    ┌─────┴──────┐
  HIT             MISS
    │               │
  Return           [Preprocessor] ── Clean & normalize
  cached                │
  result (instant)      [Run Analyzers in PARALLEL]
                        │    ├── Text Analyzer (ML + LLM)
                        │    ├── URL Analyzer (SafeBrowsing + VirusTotal)
                        │    └── Image Analyzer (Claude Vision)
                        │
                        [AI Wrapper] ── Fuse scores + generate explanation
                        │
                        [Cache Result] ── Store in Redis (TTL: 1hr)
                        │
                        [Return JSON Response]
                        { verdict, confidence, reasons[] }
```

---

## 🔬 Real Example: Text Analysis Flow

**Input:**
> "BREAKING!!! Drink hot water with lemon to CURE COVID!!! DOCTORS DONT WANT YOU TO KNOW! Share before deleted!!!"

**Step 1 — ML Model (50ms):**
- TF-IDF sees: 'BREAKING', 'CURE', 'DONT WANT YOU TO KNOW', 'Share before deleted'
- These are high-weight "fake" signal words
- Output: `{ label: 'fake', prob: 0.91 }` → **+40 points**

**Step 2 — LLM Claude (1.2s):**
- Detects: 'BREAKING!!!' → urgency/fear manipulation → **+10 pts**
- Detects: 'DOCTORS DONT WANT YOU TO KNOW' → conspiracy framing → **+10 pts**
- Detects: 'Share before deleted' → viral pressure → **+8 pts**
- Detects: Zero sources cited → **+10 pts**

**Step 3 — AI Wrapper:**
- Raw score = 40 + 10 + 10 + 8 + 10 = **78**
- LLM adjustment: +5 → **Final score = 83**
- Verdict: 🔴 **High Risk** (≥60)

**Final Response:**
```json
{
  "verdict": "High Risk",
  "confidence": 83,
  "reasons": [
    "Emotional manipulation: urgency and fear language detected",
    "Conspiracy framing: uses anti-establishment rhetoric",
    "Viral pressure: demands sharing before deletion",
    "No credible source: no doctor, study, or organization cited",
    "ML model flagged as fake with 91% confidence"
  ]
}
```

---

## 🏗️ System Architecture (5 Layers)

```
┌─────────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                          │
│       Web App (Next.js)      Mobile App (Flutter)            │
│       WhatsApp-style chat UI  ←→  Real-time WebSocket        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS / WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│                    API GATEWAY LAYER                          │
│ FastAPI (Python)  │  Rate Limiting  │  Auth (JWT)  │  CORS   │
└──┬────────────┬───────────────┬──────────────┬──────────────┘
   │            │               │              │
┌──▼───┐  ┌────▼───┐  ┌────────▼──┐  ┌────────▼────────┐
│ TEXT  │  │  URL   │  │  IMAGE    │  │  VIDEO          │
│ANALYZ│  │ANALYZER│  │ ANALYZER  │  │ ANALYZER        │
│TF-IDF│  │SafeBrw │  │NSFW+Meta  │  │Frame Sampling   │
│+ LLM │  │VTotal  │  │+LLM Visn  │  │+ Image Pipeline │
└──┬───┘  └────┬───┘  └────────┬──┘  └────────┬────────┘
   └────────────┴──────────────┴───────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 AI WRAPPER (Decision Engine)                  │
│ Score Fusion  │  Confidence Calc  │  LLM Explanation Gen     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   DATA & CACHE LAYER                         │
│  PostgreSQL (history)  │  Redis (cache)  │  S3 (media)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Complete Tech Stack

### Backend
| Component | Technology | Why |
|:---|:---|:---|
| API Framework | **FastAPI (Python)** | Async-native, auto Swagger docs, fastest Python API |
| Server | Uvicorn + Gunicorn | Async + multi-worker production |
| ML Model | **scikit-learn** (TF-IDF + Logistic Regression) | Fast, no GPU needed, trains in minutes |
| LLM | **Claude 3.5 Sonnet** (Anthropic API) | Best structured output, lowest hallucination |
| Database | **PostgreSQL 16** | Stores analysis history, user sessions |
| Cache | **Redis 7** | SHA-256 hash lookup for instant repeated results |
| Auth | PyJWT | Lightweight JWT tokens |

### Frontend (Web)
| Component | Technology | Why |
|:---|:---|:---|
| Framework | **Next.js 14** (App Router) | SSR + SSG + API routes in one |
| Styling | **Tailwind CSS + shadcn/ui** | Utility-first, pre-built components |
| State | **Zustand** | Lightweight, no boilerplate |
| Real-time | **Socket.IO** | Live analysis progress streaming |
| Animation | **Framer Motion** | Smooth result animations |
| Charts | **Recharts** | Confidence gauges, risk charts |

### Frontend (Mobile)
| Component | Technology | Why |
|:---|:---|:---|
| Framework | **Flutter 3 (Dart)** | Pixel-perfect UI, compiled to native ARM, you already know it |
| State Mgmt | **Riverpod** | Familiar from NidhiSetu, reactive & testable |
| HTTP Client | **Dio** | Interceptors, cancel tokens, FormData support |
| Camera/File | **image_picker** | One-line image/video selection on iOS & Android |
| Navigation | **GoRouter** | Declarative routing with deep link support |
| Charts | **fl_chart** | Beautiful animated charts for risk scores |
| WhatsApp Share | **share_plus** | Share content directly from/to WhatsApp |
| Animations | **Built-in Flutter** | Implicit & explicit animations, no extra library |

### External APIs
| API | Purpose |
|:---|:---|
| Google Safe Browsing (free) | Detects phishing, malware URLs |
| VirusTotal (free tier) | Scans URL against 70+ antivirus engines |
| WhoisXMLAPI (free) | Domain age check |
| Sightengine (free tier) | Image NSFW/violence detection |

---

## 📁 Project Structure

```
WhatsaapMisLEADING/
├── backend/
│   ├── main.py                  # FastAPI app factory
│   ├── config.py                # Environment settings
│   ├── api/
│   │   └── v1/
│   │       ├── analyze.py       # Main analysis endpoint
│   │       ├── auth.py          # JWT auth
│   │       ├── history.py       # Analysis history
│   │       └── stats.py         # Dashboard stats
│   ├── analyzers/
│   │   ├── text_analyzer.py     # TF-IDF + LR classifier
│   │   ├── url_analyzer.py      # SafeBrowsing + VirusTotal
│   │   ├── image_analyzer.py    # Sightengine + Claude Vision
│   │   └── video_analyzer.py    # Frame extraction + analysis
│   ├── ai_wrapper/
│   │   ├── wrapper.py           # Score fusion + verdict
│   │   ├── llm_explainer.py     # Claude API prompts
│   │   └── scoring.py           # Weighted scoring matrix
│   ├── ml/
│   │   ├── train.py             # One-time training script
│   │   ├── model.pkl            # Trained model
│   │   └── vectorizer.pkl       # TF-IDF vectorizer
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── session.py           # Async DB session
│   └── cache/
│       └── redis_client.py      # Redis helpers
├── web/                         # Next.js 14 frontend
│   ├── app/
│   │   ├── page.tsx             # Landing page
│   │   ├── chat/page.tsx        # WhatsApp-style chat UI
│   │   ├── result/[id]/page.tsx # Result detail page
│   │   └── dashboard/page.tsx   # Analytics dashboard
│   └── components/
│       ├── ChatBubble.tsx
│       ├── VerdictCard.tsx
│       └── InputBar.tsx
└── mobile/                      # Flutter + Dart
    ├── lib/
    │   ├── main.dart             # App entry point
    │   ├── screens/
    │   │   ├── home_screen.dart   # Input + camera button
    │   │   ├── chat_screen.dart   # WhatsApp-style chat UI
    │   │   ├── result_screen.dart # Verdict detail
    │   │   └── dashboard_screen.dart
    │   ├── providers/             # Riverpod state
    │   ├── services/              # API client (Dio)
    │   └── widgets/               # VerdictCard, ChatBubble
    └── pubspec.yaml
```

---

## 📅 Build Phases (12-Hour Hackathon)

### Phase 1: Foundation (Hours 1-3)
> [!IMPORTANT]
> This phase creates the backbone. Nothing works without this.

| Step | Task | Details |
|:---|:---|:---|
| 1 | Project Setup | Create folders, install dependencies, configure `.env` |
| 2 | Train ML Model | Download LIAR dataset, run `train.py`, verify `model.pkl` |
| 3 | Core FastAPI App | `main.py` with CORS, model loading, `/analyze` endpoint |

### Phase 2: Analyzers (Hours 3-6)
> [!TIP]
> Each analyzer runs independently and in parallel via `asyncio.gather()`

| Step | Task | Details |
|:---|:---|:---|
| 4 | Text Analyzer | Load model, predict, return probability dict |
| 5 | URL Analyzer | Google SafeBrowsing + VirusTotal + WHOIS parallel calls |
| 6 | LLM Integration | Claude API with structured prompt, returns JSON |
| 7 | AI Wrapper | Scoring matrix + verdict logic + reason extraction |

### Phase 3: Frontend (Hours 6-10)
> [!TIP]
> The chat UI is the "wow factor" for judges

| Step | Task | Details |
|:---|:---|:---|
| 8 | Chat UI | WhatsApp-style bubbles, VerdictCard, InputBar |
| 9 | Real-Time Progress | WebSocket streaming: "Checking ML... Running LLM..." |

### Phase 4: Polish (Hours 10-12)

| Step | Task | Details |
|:---|:---|:---|
| 10 | Image/Video Support | Cloudinary upload + Claude Vision analysis |
| 11 | Redis Caching | SHA-256 hash → instant response for repeated content |
| 12 | Mobile App | Flutter app with camera, share handler, WhatsApp deep link |
| 13 | Deploy | Railway (backend) + Vercel (frontend) |

---

## 🔑 Environment Variables Needed

```env
# AI Keys
ANTHROPIC_API_KEY=sk-ant-...

# URL Security APIs
GOOGLE_SAFE_BROWSING_KEY=AIza...
VIRUSTOTAL_API_KEY=...

# Image Analysis
SIGHTENGINE_API_USER=...
SIGHTENGINE_API_SECRET=...

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/misinfo

# Cache
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET=your-random-secret-key

# App
ENVIRONMENT=development
```

---

## 🎯 API Endpoints

| Endpoint | Method | Description |
|:---|:---|:---|
| `/api/v1/analyze` | POST | Main analysis (text/url/image/video) |
| `/api/v1/result/:id` | GET | Fetch stored result |
| `/api/v1/history` | GET | Paginated analysis history |
| `/api/v1/feedback` | POST | User marks verdict correct/wrong |
| `/api/v1/stats` | GET | Dashboard aggregate stats |
| `/ws/analysis/:id` | WebSocket | Real-time analysis progress |

---

## 🎪 Demo Strategy

1. Open chat UI → paste a **real fake WhatsApp forward** → show HIGH RISK with reasons
2. Paste a **BBC headline** → show LOW RISK
3. Upload an **AI-generated image** → show suspicious detection
4. Open dashboard → show trend charts

> [!WARNING]
> Pre-cache 5-6 test inputs before presenting to avoid LLM rate limits during demo!
