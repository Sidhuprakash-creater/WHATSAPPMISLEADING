# 🛡️ MisLEADING — Multi-Modal AI Misinformation Detection

> Real-time, explainable AI platform that detects misinformation across text, URLs, images, and video.

## ✨ Features
- 🧠 **Hybrid AI** — ML model (fast) + LLM reasoning (deep)
- 💬 **WhatsApp-style** chat interface
- 📊 **Explainable verdicts** — not just labels, but reasons
- 🔗 **Multi-modal** — text, URL, image, video analysis
- ⚡ **< 3 second** response time with Redis caching

## 🏗️ Architecture
```
User Input → Input Router → Parallel Analyzers → AI Wrapper → Verdict
                             ├── Text (ML + LLM)
                             ├── URL (SafeBrowsing + VirusTotal)
                             ├── Image (Claude Vision)
                             └── Video (Frame Extraction)
```

## 🛠️ Tech Stack
| Layer | Technology |
|:---|:---|
| Backend | FastAPI + Python |
| AI/ML | scikit-learn + Claude 3.5 Sonnet |
| Web | Next.js 14 + Tailwind CSS |
| Mobile | Flutter + Dart |
| Database | PostgreSQL + Redis |

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Web Frontend
```bash
cd web
npm install
npm run dev
```

### Mobile
```bash
cd mobile
flutter pub get
flutter run
```

## 📄 Environment Variables
Copy `.env.example` to `.env` and fill in your API keys.

## 👥 Team
Built for hackathon by a team of 4.
