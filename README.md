# 🗳️ VoteWise — AI Election Education Platform

> An AI-powered assistant that helps users understand the U.S. election process, timelines, and steps in an interactive and easy-to-follow way.

[![CI — VoteWise](https://github.com/rdx644/VoteWise-Election-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/rdx644/VoteWise-Election-Assistant/actions)

## 📋 Chosen Vertical

**Election Process Education** — Making civic participation accessible through AI-powered interactive learning.

## 🎯 Approach and Logic

VoteWise uses **Google Gemini 2.0 Flash** as its core AI engine, combined with a structured election knowledge base to deliver **adaptive, personalized education** about the election process.

### Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Frontend (HTML/CSS/JS)               │
│  Dashboard │ AI Chat │ Timeline │ Quiz │ Readiness    │
└─────────────────────┬────────────────────────────────┘
                      │ REST API
┌─────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐            │
│  │ Gemini AI│ │ Quiz      │ │ Analytics│            │
│  │ Service  │ │ Engine    │ │ Service  │            │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘            │
│       │             │            │                   │
│  ┌────▼─────────────▼────────────▼─────┐            │
│  │     Google Cloud Services Layer      │            │
│  │  Logging│Storage│SecretMgr│Firestore │            │
│  └──────────────────────────────────────┘            │
└──────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Adaptive Learning Engine** — The AI adjusts response complexity based on user's learning level (Beginner → Intermediate → Advanced)
2. **Structured Knowledge Base** — 9-phase election timeline with curated educational content, not just raw AI generation
3. **Gamified Learning** — XP points, badges, leaderboard, and difficulty tiers to maintain engagement
4. **Civic Readiness Assessment** — Personalized checklist based on user's actual preparation status
5. **Dual-Mode Database** — InMemory for development, Cloud Firestore for production via abstract `DatabaseProtocol`

## 🚀 How the Solution Works

### Features

| Feature | Description |
|---------|-------------|
| **💬 AI Chat Assistant** | Gemini-powered contextual Q&A about elections with adaptive complexity |
| **📅 Election Timeline** | Interactive 9-step visual journey from registration to inauguration |
| **🧠 Adaptive Quizzes** | Multi-difficulty questions with instant feedback, XP, and badges |
| **✅ Civic Readiness** | Personalized voter preparation assessment with actionable recommendations |
| **📊 Analytics Dashboard** | Engagement metrics, leaderboard, and system health monitoring |
| **🔊 Text-to-Speech** | Google Cloud TTS for audio narration of election information |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check |
| `POST` | `/api/chat` | AI chat message |
| `GET` | `/api/timeline` | Full election timeline |
| `GET` | `/api/timeline/steps` | All election steps |
| `POST` | `/api/timeline/readiness` | Civic readiness assessment |
| `POST` | `/api/quiz/generate` | Generate adaptive quiz |
| `POST` | `/api/quiz/answer` | Submit quiz answer |
| `POST` | `/api/quiz/complete/{id}` | Complete quiz and get results |
| `GET` | `/api/analytics/summary` | Platform analytics |
| `GET` | `/api/analytics/leaderboard` | XP leaderboard |
| `GET/POST/PUT/DELETE` | `/api/users` | User CRUD |

## ☁️ Google Services Integration

| # | Service | Purpose | Module |
|---|---------|---------|--------|
| 1 | **Google Gemini 2.0 Flash** | AI chat assistant with adaptive learning | `gemini_service.py` |
| 2 | **Google Cloud TTS** | Voice narration of election steps | `tts_service.py` |
| 3 | **Google Cloud Firestore** | User data, chat history, quiz scores | `database.py` |
| 4 | **Google Cloud Storage** | Audio cache, quiz exports, analytics | `cloud_storage.py` |
| 5 | **Google Cloud Logging** | Structured event logging, latency tracking | `cloud_logging.py` |
| 6 | **Google Cloud Secret Manager** | Secure API key management | `secret_manager.py` |
| 7 | **Google Cloud Run** | Serverless container deployment | `Dockerfile` |
| 8 | **Google Cloud Build** | CI/CD pipeline | `cloudbuild.yaml` |
| 9 | **Container Registry** | Docker image storage | `cloudbuild.yaml` |

## 🛠️ Tech Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2
- **Frontend:** HTML5, CSS3 (Glassmorphism dark mode), Vanilla JavaScript
- **AI:** Google Gemini 2.0 Flash
- **Database:** InMemory (dev) / Cloud Firestore (prod)
- **Testing:** Pytest with 70%+ coverage
- **CI/CD:** GitHub Actions + Google Cloud Build
- **Deployment:** Google Cloud Run (Docker)

## 📁 Project Structure

```
election-assistant/
├── backend/
│   ├── app.py                 # FastAPI main application
│   ├── config.py              # Pydantic settings
│   ├── models.py              # Data models (20+ types)
│   ├── database.py            # InMemory + Firestore (DatabaseProtocol)
│   ├── election_data.py       # Election knowledge base (9 phases, 18 questions)
│   ├── gemini_service.py      # Google Gemini AI chat service
│   ├── quiz_engine.py         # Adaptive quiz generation + scoring
│   ├── exceptions.py          # Custom exception hierarchy (9 classes)
│   ├── middleware.py           # Rate limiting + security headers
│   ├── security.py            # Input sanitization
│   ├── analytics.py           # Engagement metrics
│   ├── cloud_logging.py       # Google Cloud Logging
│   ├── cloud_storage.py       # Google Cloud Storage
│   ├── secret_manager.py      # Google Cloud Secret Manager
│   ├── tts_service.py         # Google Cloud TTS
│   ├── routes/
│   │   ├── chat.py            # AI chat endpoints
│   │   ├── timeline.py        # Election timeline + readiness
│   │   ├── quiz.py            # Quiz generation + scoring
│   │   └── analytics.py       # Platform analytics
│   └── tests/                 # 60+ test cases
├── frontend/
│   ├── index.html             # Premium dark-mode UI
│   ├── css/style.css          # Design system (500+ lines)
│   └── js/app.js              # Interactive frontend logic
├── .github/workflows/ci.yml   # GitHub Actions CI
├── Dockerfile                 # Production container
├── cloudbuild.yaml            # Cloud Build pipeline
├── requirements.txt           # Python dependencies
└── pyproject.toml             # Project configuration
```

## ⚡ Quick Start

```bash
# Clone
git clone https://github.com/rdx644/VoteWise-Election-Assistant.git
cd VoteWise-Election-Assistant

# Setup
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Configure (optional — works without API key using fallback responses)
copy .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run
uvicorn backend.app:app --reload --port 8080

# Test
pytest backend/tests/ -v
```

## 🔑 Assumptions

1. Users are primarily learning about U.S. federal elections (but architecture supports localization)
2. The AI assistant operates in a **nonpartisan, educational** capacity
3. Quiz questions are curated for accuracy and educational value
4. The system works **fully offline** (without Gemini API key) using structured fallback responses
5. Cloud services degrade gracefully — all features work locally without GCP

## 📊 Scoring Criteria Alignment

| Criteria | Implementation |
|----------|----------------|
| **Code Quality** | Modular architecture, type annotations, docstrings, Pydantic models |
| **Security** | Rate limiting, CSP headers, input sanitization, non-root Docker, Secret Manager |
| **Efficiency** | LRU caching, lazy model init, async endpoints, connection pooling |
| **Testing** | 60+ test cases, 70%+ coverage, CI pipeline |
| **Accessibility** | WCAG AA, semantic HTML, ARIA labels, keyboard navigation, `prefers-reduced-motion` |
| **Google Services** | 9 integrated Google Cloud services with graceful degradation |

## 📄 License

MIT License — Built for the Google Cloud AI Hackathon
