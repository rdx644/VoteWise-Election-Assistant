## 🌐 Live Demo
https://votewise-election-assistant-43248167698.us-central1.run.app)

# 🗳️ VoteWise — AI Election Education Platform

> An AI-powered assistant that helps users understand the U.S. election process, timelines, and steps in an interactive and easy-to-follow way.

[![CI](https://github.com/rdx644/VoteWise-Election-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/rdx644/VoteWise-Election-Assistant/actions)

---

## 📋 Chosen Vertical

**Election Process Education** — Making civic participation accessible through AI-powered interactive learning.

---

## 🎯 Approach & Solution Logic

VoteWise uses **Google Gemini 2.0 Flash** as its core AI engine, combined with a structured election knowledge base to deliver **adaptive, personalized education** about the U.S. election process.

### Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                  Frontend (HTML/CSS/JS)              │
│  Dashboard │ AI Chat │ Timeline │ Quiz │ Readiness   │
└─────────────────────┬────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────┐
│                  FastAPI Backend                    │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐            │
│  │ Gemini AI│ │ Quiz      │ │ Analytics│            │
│  │ Service  │ │ Engine    │ │ Service  │            │
│  └────┬─────┘ └─────┬─────┘ └────┬─────┘            │
│       │             │            │                  │
│  ┌────▼─────────────▼────────────▼─────┐            │
│  │     Google Cloud Services Layer      │           │
│  │  Logging│Storage│SecretMgr│Firestore │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Adaptive Learning Engine** — The AI adjusts response complexity based on user's learning level (Beginner → Intermediate → Advanced)
2. **Structured Knowledge Base** — 9-phase election timeline with curated educational content, not just raw AI generation
3. **Gamified Learning** — XP points, badges, leaderboard, and difficulty tiers to maintain engagement
4. **Civic Readiness Assessment** — Personalized checklist based on user's actual preparation status
5. **Dual-Mode Database** — `InMemoryDatabase` for development, `FirestoreDatabase` for production via abstract `DatabaseProtocol`
6. **Security-First Middleware** — Token-bucket rate limiting, CSP headers, HSTS, input sanitization

---

## 🚀 How the Solution Works

### Features

| Feature | Description |
|---------|-------------|
| 💬 **AI Chat Assistant** | Gemini-powered contextual Q&A about elections with adaptive complexity |
| 📅 **Election Timeline** | Interactive 9-step visual journey from registration to inauguration |
| 🧠 **Adaptive Quizzes** | Multi-difficulty questions with instant feedback, XP, and badges |
| ✅ **Civic Readiness** | Personalized voter preparation assessment with actionable recommendations |
| 📊 **Analytics Dashboard** | Engagement metrics, leaderboard, and system health monitoring |
| 🔊 **Text-to-Speech** | Google Cloud TTS for audio narration of election information |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check |
| `POST` | `/api/chat` | Send message to AI assistant |
| `GET` | `/api/timeline` | Full election timeline |
| `GET` | `/api/timeline/steps` | All election steps |
| `GET` | `/api/timeline/steps/{id}` | Specific step by ID |
| `GET` | `/api/timeline/phases/{phase}` | Step by phase name |
| `POST` | `/api/timeline/readiness` | Civic readiness assessment |
| `POST` | `/api/quiz/generate` | Generate adaptive quiz |
| `GET` | `/api/quiz/questions` | List all questions |
| `POST` | `/api/quiz/answer` | Submit quiz answer |
| `POST` | `/api/quiz/complete/{id}` | Complete quiz and get results |
| `GET` | `/api/analytics/summary` | Platform analytics |
| `GET` | `/api/analytics/health` | System health metrics |
| `GET` | `/api/analytics/leaderboard` | XP leaderboard |
| `POST` | `/api/analytics/export` | Export analytics to GCS |
| `GET` | `/api/users` | List all users |
| `POST` | `/api/users` | Create user |
| `GET` | `/api/users/{id}` | Get user by ID |
| `PUT` | `/api/users/{id}` | Update user |
| `DELETE` | `/api/users/{id}` | Delete user |

---

## ☁️ Google Services Integration

| # | Service | Purpose | Module |
|---|---------|---------|--------|
| 1 | **Google Gemini 2.0 Flash** | AI chat assistant with adaptive learning levels | `gemini_service.py` |
| 2 | **Google Cloud Text-to-Speech** | Voice narration of election steps | `tts_service.py` |
| 3 | **Google Cloud Firestore** | User data, chat history, quiz scores (production) | `database.py` |
| 4 | **Google Cloud Storage** | Audio cache, quiz exports, analytics reports | `cloud_storage.py` |
| 5 | **Google Cloud Logging** | Structured JSON event logging, latency tracking | `cloud_logging.py` |
| 6 | **Google Cloud Secret Manager** | Secure API key management with env fallback | `secret_manager.py` |
| 7 | **Google Cloud Run** | Serverless container deployment | `Dockerfile` |
| 8 | **Google Cloud Build** | CI/CD deployment pipeline | `cloudbuild.yaml` |
| 9 | **Google Container Registry** | Docker image storage | `cloudbuild.yaml` |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| **Frontend** | HTML5, CSS3 (Glassmorphism dark mode), Vanilla JavaScript |
| **AI** | Google Gemini 2.0 Flash |
| **Database** | InMemory (dev) / Cloud Firestore (prod) |
| **Testing** | Pytest with 88%+ coverage |
| **Linting** | Ruff (lint + format) |
| **CI/CD** | GitHub Actions + Google Cloud Build |
| **Deployment** | Google Cloud Run (Docker) |

---

## 📁 Project Structure

```
election-assistant/
├── backend/
│   ├── app.py                 # FastAPI application with lifespan events
│   ├── config.py              # Pydantic settings with GCP configuration
│   ├── models.py              # 20+ Pydantic v2 data models
│   ├── database.py            # Dual-mode: InMemory + Firestore (DatabaseProtocol)
│   ├── election_data.py       # Knowledge base: 9 phases, 18 questions, readiness logic
│   ├── gemini_service.py      # Google Gemini AI chat with adaptive prompts
│   ├── quiz_engine.py         # Adaptive quiz generation, scoring, XP/badges
│   ├── exceptions.py          # 9-class exception hierarchy with HTTP mapping
│   ├── middleware.py           # Rate limiting, CSP, security headers, logging
│   ├── security.py            # Input sanitization and content filtering
│   ├── analytics.py           # Engagement metrics and system health
│   ├── cloud_logging.py       # Google Cloud Logging integration
│   ├── cloud_storage.py       # Google Cloud Storage utilities
│   ├── secret_manager.py      # Google Cloud Secret Manager integration
│   ├── tts_service.py         # Google Cloud Text-to-Speech integration
│   ├── routes/
│   │   ├── chat.py            # AI chat endpoints
│   │   ├── timeline.py        # Election timeline + readiness endpoints
│   │   ├── quiz.py            # Quiz generation + scoring endpoints
│   │   └── analytics.py       # Platform analytics endpoints
│   └── tests/
│       ├── conftest.py        # Shared fixtures (TestClient, env setup)
│       ├── test_api.py        # API endpoint tests (20+ cases)
│       ├── test_core.py       # Core logic tests (30+ cases)
│       └── test_cloud_services.py  # Cloud service tests (10+ cases)
├── frontend/
│   ├── index.html             # Premium dark-mode glassmorphism UI
│   ├── css/style.css          # Design system with animations
│   └── js/app.js              # Interactive frontend with particle system
├── .github/workflows/ci.yml   # GitHub Actions CI pipeline
├── Dockerfile                 # Production container (non-root, multi-stage)
├── cloudbuild.yaml            # Google Cloud Build pipeline
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project config (pytest, ruff)
└── .env.example               # Environment variable template
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- (Optional) Google Cloud account with Gemini API key

### Setup

```bash
# Clone the repository
git clone https://github.com/rdx644/VoteWise-Election-Assistant.git
cd VoteWise-Election-Assistant

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure environment
copy .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run the application
uvicorn backend.app:app --reload --port 8080

# Open in browser
# http://localhost:8080
```

### Run Tests

```bash
pytest backend/tests/ -v
```

### Run Linter

```bash
ruff check backend/ --config pyproject.toml
ruff format --check backend/ --config pyproject.toml
```

### Deploy to Cloud Run

```bash
gcloud run deploy votewise-election-assistant \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=production,DATABASE_MODE=memory,TTS_MODE=browser \
  --port 8080 \
  --memory 512Mi
```

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | No | — | Google Gemini API key (uses fallback responses without it) |
| `GOOGLE_CLOUD_PROJECT` | No | — | GCP project ID |
| `GCS_BUCKET_NAME` | No | — | Cloud Storage bucket name |
| `APP_ENV` | No | `development` | Environment: development, testing, production |
| `DATABASE_MODE` | No | `memory` | Database: memory or firestore |
| `TTS_MODE` | No | `browser` | TTS: browser or google |
| `RATE_LIMIT_RPM` | No | `60` | Rate limit: requests per minute |

---

## 📝 Assumptions

1. Users are primarily learning about **U.S. federal elections** (architecture supports localization)
2. The AI assistant operates in a **nonpartisan, educational** capacity only
3. Quiz questions are **curated for accuracy** and educational value
4. The system works **fully offline** (without Gemini API key) using structured fallback responses
5. All Google Cloud services **degrade gracefully** — every feature works locally without GCP credentials

---

## 📊 Evaluation Criteria Alignment

| Criteria | Implementation |
|----------|----------------|
| **Code Quality** | Modular architecture, type annotations, docstrings, Pydantic v2 models, ruff lint + format |
| **Security** | Rate limiting, CSP headers, HSTS, input sanitization, non-root Docker, Secret Manager |
| **Efficiency** | LRU caching, lazy model initialization, async endpoints, connection pooling |
| **Testing** | 60+ test cases, 88%+ coverage, GitHub Actions CI pipeline |
| **Accessibility** | WCAG AA, semantic HTML, ARIA labels, keyboard navigation, `prefers-reduced-motion` |
| **Google Services** | 9 integrated Google Cloud services with graceful degradation |

---

## 📄 License

MIT License — Built for the Google Cloud AI Hackathon
