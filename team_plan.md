# 👥 Team Plan — 4 Members, 12-Hour Hackathon
## ML & LLM Split Strategy

---

## 🎯 Role Assignments

```
┌──────────────┬──────────────────────────────────────────────────┐
│  MEMBER 1    │  🧠 ML Engineer (Fast Brain)                    │
│              │  Trains model → then helps Backend after Hour 4  │
├──────────────┼──────────────────────────────────────────────────┤
│  MEMBER 2    │  🤖 LLM + AI Wrapper Engineer (Deep Brain)      │
│              │  Claude API, scoring, image/video analysis       │
├──────────────┼──────────────────────────────────────────────────┤
│  MEMBER 3    │  ⚡ Backend API Developer (FastAPI)              │
│              │  APIs, DB, Redis, URL analyzer, deployment       │
├──────────────┼──────────────────────────────────────────────────┤
│  MEMBER 4    │  🎨📱 Full Frontend + Presenter (+ Antigravity)  │
│              │  Web + Mobile + Backend Access + AI-Assisted Dev  │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 👤 Member 1 — 🧠 ML Engineer → Then Backend Helper

> [!TIP]
> ML work finishes by Hour 4. After that, Member 1 **joins Member 3** on backend tasks (URL analyzer, Redis caching, testing).

| Hours | Task | Deliverable |
|:---|:---|:---|
| 1-2 | Download LIAR dataset, write & run `ml/train.py` | `model.pkl` + `vectorizer.pkl` ready |
| 2-3 | Build `analyzers/text_analyzer.py` — load model, predict, return dict | Text analyzer working |
| 3-4 | Test text analyzer with 10+ sample inputs, tune accuracy | Reliable predictions |
| **4-6** | **🔄 Switch to Backend:** Build `analyzers/url_analyzer.py` — SafeBrowsing + VirusTotal + WHOIS | URL analyzer working |
| **6-8** | **🔄 Backend:** Build `cache/redis_client.py` — SHA-256 hashing + Redis caching | Cache working |
| **8-10** | **🔄 Backend:** Help with integration testing, fix edge cases | End-to-end tested |
| 10-12 | Help Member 3 deploy, test production | Everything deployed |

### Files Owned
```
backend/
├── ml/
│   ├── train.py              ← writes this
│   ├── model.pkl             ← generates this
│   └── vectorizer.pkl        ← generates this
├── analyzers/
│   ├── text_analyzer.py      ← writes this
│   └── url_analyzer.py       ← writes this (after Hour 4)
└── cache/
    └── redis_client.py       ← writes this (after Hour 6)
```

### Git Branch: `feature/ml-model`

---

## 👤 Member 2 — 🤖 LLM + AI Wrapper Engineer

> [!IMPORTANT]
> This is the **most complex** role. Member 2 builds the "reasoning" layer that makes this project unique.

| Hours | Task | Deliverable |
|:---|:---|:---|
| 1-2 | Study Claude API docs, set up Anthropic SDK, test basic call | API connection working |
| 2-4 | Build `ai_wrapper/llm_explainer.py` — system prompt + user prompt + JSON parsing | LLM returns structured reasons[] |
| 4-5 | Build `ai_wrapper/scoring.py` — weighted scoring matrix (all point values) | Scoring engine working |
| 5-6 | Build `ai_wrapper/wrapper.py` — orchestrates all analyzers, fuses scores, generates verdict | Full AI pipeline end-to-end |
| 6-8 | Build `analyzers/image_analyzer.py` — Claude Vision for image misinformation detection | Image analysis working |
| 8-10 | Build `analyzers/video_analyzer.py` — frame extraction (OpenCV) + image pipeline | Video support |
| 10-12 | Fine-tune LLM prompts, fix JSON parsing edge cases, optimize scoring weights | Polished AI output |

### Files Owned
```
backend/
├── ai_wrapper/
│   ├── wrapper.py            ← writes this
│   ├── llm_explainer.py      ← writes this
│   └── scoring.py            ← writes this
└── analyzers/
    ├── image_analyzer.py     ← writes this
    └── video_analyzer.py     ← writes this
```

### Git Branch: `feature/llm-wrapper`

---

## 👤 Member 3 — ⚡ Backend API Developer

| Hours | Task | Deliverable |
|:---|:---|:---|
| 1-2 | Create repo, project skeleton, `venv`, install all deps, `.env`, `config.py` | Project structure ready |
| 2-3 | Build `main.py` — FastAPI app, CORS, startup events, model loading | `localhost:8000/docs` live |
| 3-5 | Build `api/v1/analyze.py` — POST endpoint + Pydantic models + input router | `/analyze` endpoint working |
| 5-6 | Build `api/v1/auth.py` — JWT login + refresh | Auth working |
| 6-7 | Build `db/models.py` + `session.py` — SQLAlchemy + PostgreSQL | DB connected |
| 7-8 | Build `api/v1/history.py` + `stats.py` — paginated history + dashboard stats | History & stats APIs |
| 8-9 | Build `api/websocket.py` — real-time analysis progress | WebSocket live |
| 9-10 | Integration with Member 1 & 2's analyzers + end-to-end test | Full pipeline working |
| 10-12 | Deploy to Railway (backend + PostgreSQL + Redis) | Production live |

### Files Owned
```
backend/
├── main.py                   ← writes this
├── config.py                 ← writes this
├── requirements.txt          ← writes this
├── Dockerfile                ← writes this
├── .env.example              ← writes this
├── api/
│   ├── v1/
│   │   ├── analyze.py        ← writes this
│   │   ├── auth.py           ← writes this
│   │   ├── history.py        ← writes this
│   │   └── stats.py          ← writes this
│   └── websocket.py          ← writes this
└── db/
    ├── models.py             ← writes this
    ├── session.py            ← writes this
    └── crud.py               ← writes this
```

### Git Branch: `feature/backend-api`

---

## 👤 Member 4 — 🎨📱 Full Frontend + Presenter (Antigravity-Powered)

> [!IMPORTANT]
> **Superpower:** Member 4 uses **Antigravity AI** as a pair programmer + has **full backend access**. This means:
> - 🤖 AI generates components, screens, API clients at 10x speed
> - 🔧 Can directly debug/fix backend issues without waiting for Member 3
> - 🔗 Can wire frontend-to-backend integration independently
> - ⚡ Handles both Web + Mobile + Backend fixes = true full-stack

| Hours | Task | Deliverable |
|:---|:---|:---|
| 1-2 | Setup Next.js + Flutter projects, install all deps (via Antigravity) | Both projects running |
| 2-4 | **Web:** Landing page + Chat page — Antigravity builds components fast | Web hero + chat UI |
| 4-6 | **Web:** VerdictCard, RiskGauge, Dashboard — AI generates charts/animations | All web pages done |
| 6-7 | **Web + Backend:** Connect to real API, fix any backend bugs directly | Web fully working end-to-end |
| 7-9 | **Flutter:** Home + Chat + VerdictCard — reuse design patterns from web | Mobile core UI done |
| 9-10 | **Flutter + Backend:** Result screen, WebSocket integration, fix API issues | Mobile fully connected |
| 10-11 | **Prepare PPT** — 5 slides: Problem → Solution → Architecture → Demo → Impact | Slides ready |
| 11-12 | **Practice demo** + deploy web to Vercel + build Flutter APK | Demo polished |

### Antigravity Workflow for Member 4
```
Member 4's Workflow:
┌─────────────────────────────────────────────────────┐
│  "Build me a WhatsApp-style chat page"              │
│           ↓ (Antigravity generates code)            │
│  ChatBubble.tsx + VerdictCard.tsx + InputBar.tsx     │
│           ↓                                         │
│  "Connect this to POST /api/v1/analyze"             │
│           ↓ (Antigravity writes API client)         │
│  api.ts with Axios + React Query integration        │
│           ↓                                         │
│  "The API returns 500 error, fix it"                │
│           ↓ (Has backend access!)                   │
│  Antigravity reads backend code → fixes the bug     │
│           ↓                                         │
│  End-to-end working without waiting for anyone!     │
└─────────────────────────────────────────────────────┘
```

### Files Owned
```
web/                              # Next.js (via Antigravity)
├── app/                          ← All pages
├── components/                   ← All components
└── lib/                          ← API client + store

mobile/                           # Flutter (via Antigravity)
├── lib/
│   ├── screens/                  ← All 4 screens
│   ├── providers/                ← Riverpod state
│   ├── services/api_service.dart ← Dio client
│   └── widgets/                  ← VerdictCard, ChatBubble

backend/ (READ + FIX access)      # Can debug & fix directly
├── api/                          ← Fix endpoint bugs
├── main.py                       ← Fix CORS, startup issues
└── config.py                     ← Fix env variable issues
```

### Git Branches: `feature/web-frontend` + `feature/mobile-flutter`

---

## 🔀 GitHub Workflow

### Step 1: Member 3 Creates Repo (Hour 1, First Thing)
```bash
git init
git remote add origin https://github.com/YOUR_TEAM/WhatsaapMisLEADING.git
# Create skeleton folders → push to main
```

### Step 2: Everyone Clones & Branches
```bash
git clone https://github.com/YOUR_TEAM/WhatsaapMisLEADING.git
cd WhatsaapMisLEADING

# Member 1: git checkout -b feature/ml-model
# Member 2: git checkout -b feature/llm-wrapper
# Member 3: git checkout -b feature/backend-api
# Member 4: git checkout -b feature/web-frontend (and later feature/mobile-flutter)
```

### Step 3: Commit → Push → PR → Merge
```bash
# Commit often (every 30 min):
git add . && git commit -m "feat: add text analyzer"
git push origin feature/ml-model

# When feature done → Create PR on GitHub → 1 review → Merge
```

### Step 4: Stay Synced
```bash
git checkout main && git pull origin main
git checkout feature/your-branch && git merge main
```

---

## 🔗 Integration Dependency Map

```
Member 1 (ML Model)        Member 2 (LLM + Wrapper)
   │                              │
   │ model.pkl (Hour 3)           │ wrapper.py (Hour 6)
   │ text_analyzer.py             │ llm_explainer.py
   │ url_analyzer.py (Hour 6)     │ scoring.py
   │                              │ image_analyzer.py
   │                              │
   └──────── both merge into ─────┘
                  │
            Member 3 (Backend)
            wires everything into /api/v1/analyze
                  │
         API ready by Hour 6
                  │
          ┌───────┴────────┐
          ▼                ▼
    Member 4 (Web)   Member 4 (Mobile)
    + Antigravity     + Antigravity
          │                │
          └──── can also ──┘
               fix backend
               bugs directly!
```

### 🔔 Critical Sync Points

| Hour | Event | Action |
|:---|:---|:---|
| **Hour 2** | Member 3 has FastAPI skeleton live | Share `localhost:8000/docs` URL with team |
| **Hour 3** | Member 1 has `model.pkl` ready | Merge `feature/ml-model` → Member 3 integrates |
| **Hour 4** | Member 1 finishes ML, switches to Backend | Member 1 joins Member 3's tasks |
| **Hour 6** | Member 2 has full AI pipeline ready | Merge `feature/llm-wrapper` → Member 3 wires into API |
| **Hour 6** | API fully working | Member 4 connects frontend + fixes any API bugs with Antigravity |
| **Hour 10** | Everything connected | All 4 test end-to-end together |
| **Hour 11** | All PRs merged | Member 3 deploys, Member 4 rehearses demo |

---

## ⚠️ Golden Rules

> [!CAUTION]
> 1. **NEVER push to `main` directly** — always branch + PR
> 2. **NEVER commit `.env`** — add to `.gitignore` immediately
> 3. **Commit every 30 minutes** — small commits, clear messages
> 4. **Mock data first** — Member 4 doesn't wait for backend, uses fake JSON
> 5. **Member 1 switches after Hour 4** — don't sit idle, help backend!

---

## 🏁 Final Checklist (Hour 12)

- [ ] All branches merged to `main`
- [ ] Backend deployed on Railway
- [ ] Web deployed on Vercel
- [ ] Flutter APK built
- [ ] 5 test inputs pre-cached
- [ ] Demo script rehearsed 2x
- [ ] PPT ready (5 slides max)
- [ ] `.env` keys working on production
