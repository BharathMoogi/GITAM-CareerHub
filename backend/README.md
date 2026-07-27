# GITAM CareerHub — Production Backend API

> **Production-ready AI-powered career platform for GITAM University**  
> 111 REST endpoints • 91 tests passing • 8 engine modules • Full DevOps stack

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                     GITAM CareerHub Backend                          │
│                                                                      │
│  Nginx (TLS/HTTP2/Gzip/Rate Limit)                                   │
│     │                                                                │
│     ├── FastAPI (4 uvicorn workers, 111 endpoints)                   │
│     │     ├── Authentication + Refresh Token Rotation                │
│     │     ├── Student Profile & Academic Roadmap                     │
│     │     ├── Learning Engine (Courses, Skills)                      │
│     │     ├── Project Intelligence Engine                            │
│     │     ├── Certification Intelligence Engine                      │
│     │     ├── Industry Intelligence Engine                           │
│     │     ├── Internship & Placement Engine (5-stage pipeline)       │
│     │     ├── AI Mentor Engine (6 LLM providers, 10 Jinja2 prompts) │
│     │     ├── Dashboard Intelligence Engine                          │
│     │     ├── Career Gamification Engine (Level 1-6 XP system)      │
│     │     ├── Resume Intelligence Engine (ATS scoring)               │
│     │     ├── Notification Engine (5-channel Event Bus)              │
│     │     └── Enterprise Admin CMS (6 RBAC roles)                   │
│     │                                                                │
│     ├── PostgreSQL 16 (QueuePool: 20+10, pool_pre_ping)             │
│     ├── Redis 7 (Cache + Celery broker + rate limiting)              │
│     ├── Celery Worker + Beat (email queue, challenges reset)         │
│     └── Prometheus + Grafana (metrics scraping, dashboards)          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Docker 24+ and Docker Compose 2.24+
- Python 3.12+ (for local development without Docker)

### 1. Configure Environment
```bash
cp backend/.env.example backend/.env
# Edit .env with your database credentials, SECRET_KEY, etc.
```

### 2. Generate a secure SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Start the Full Production Stack
```bash
docker compose up -d
```

### 4. Access the API
| Service | URL |
|---------|-----|
| API (via Nginx) | https://localhost |
| API (direct) | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin / set GRAFANA_PASSWORD) |

---

## Local Development (without Docker)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt aiosqlite

# Copy and configure env (SQLite for local dev)
cp .env.example .env
# Set DATABASE_URL=sqlite+aiosqlite:///./dev_careerhub.db

# Start development server with hot reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Running Tests

```bash
cd backend
# Run all 91 tests
python -c "
import sys, asyncio, pathlib
sys.path.insert(0, '.')
# ... (see test runner in backend/tests/)
"

# Or individual suites
python tests/test_placement.py
python tests/test_ai_mentor.py
python tests/test_dashboard.py
python tests/test_gamification.py
python tests/test_resume.py
python tests/test_notification.py
python tests/test_cms.py
python tests/test_production.py
```

### Test Suite Coverage

| Suite | Tests | Coverage |
|-------|-------|----------|
| Internship & Placement Engine | 18 | Stage pipeline, eligibility, offer letters |
| AI Mentor Engine | 29 | LLM providers, prompt templates, streaming, RAG |
| Dashboard Intelligence | 8 | Live metrics, chart JSON, leaderboard |
| Career Gamification | 7 | XP, levels, challenges, badges, rewards |
| Resume Intelligence | 7 | ATS scoring, STAR bullets, portfolio |
| Notification Engine | 7 | Event bus, channels, preferences, email queue |
| Enterprise Admin CMS | 7 | RBAC, audit logs, approvals, versioning |
| Production Infrastructure | 8 | Feature flags, JWT, rate limiter, Redis, metrics |
| **TOTAL** | **91** | **0 failures** |

---

## Production Deployment

### Database Migration
```bash
docker compose exec api python -m alembic upgrade head
```

### Database Backup
```bash
docker compose exec postgres /usr/local/bin/db_backup.sh
```

### Horizontal Scaling (increase API workers)
```bash
docker compose up -d --scale api=3
```

### Celery Monitoring (Flower UI)
```bash
docker compose exec celery python -m celery -A app.core.celery_app flower --port=5555
```

---

## API Documentation

### Authentication
All protected endpoints require:
```
Authorization: Bearer <access_token>
```

### Refresh Token Rotation
```
POST /api/v1/auth/refresh
Body: { "refresh_token": "..." }
Returns: { "access_token": "...", "refresh_token": "...", "expires_in": 1800 }
```

### Rate Limiting
- **60 requests/minute** per IP (sliding window)
- **429 Too Many Requests** with `Retry-After` header when exceeded
- Exempt paths: `/health`, `/metrics`, `/docs`, `/redoc`

### Security Headers
Every response includes:
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: default-src 'self'; ...`

---

## Infrastructure Components

### Redis Caching
- **Default TTL**: 300s (AI chat responses, dashboard data)
- **Long TTL**: 3600s (roadmap data, company profiles)
- **Fallback**: In-memory cache when Redis is unavailable

### Connection Pooling (PostgreSQL)
| Setting | Value |
|---------|-------|
| pool_size | 20 |
| max_overflow | 10 |
| pool_timeout | 30s |
| pool_recycle | 3600s |
| pool_pre_ping | ✅ Enabled |

### Celery Background Tasks
| Task | Schedule | Queue |
|------|----------|-------|
| `process_email_queue_task` | Every 5 min | emails |
| `reset_daily_challenges` | Daily 00:00 UTC | default |
| `aggregate_admin_analytics` | Every 1 hour | default |

### Feature Flags
Toggle via environment variables — no redeploy needed:
```bash
FEATURE_AI_MENTOR=true
FEATURE_GAMIFICATION=true
FEATURE_RESUME_AI=true
FEATURE_NOTIFICATIONS=true
FEATURE_ANALYTICS=true
FEATURE_RATE_LIMITING=true
```

---

## AI Mentor — LLM Provider Configuration

Switch providers via `LLM_PROVIDER` environment variable:

| Provider | Env Variable | Key Required |
|----------|-------------|--------------|
| `mock` | — | No (default for dev) |
| `openai` | `OPENAI_API_KEY` | Yes |
| `gemini` | `GEMINI_API_KEY` | Yes |
| `claude` | `ANTHROPIC_API_KEY` | Yes |
| `groq` | `GROQ_API_KEY` | Yes |
| `azure` | `AZURE_OPENAI_API_KEY` | Yes |

---

## CI/CD Pipeline (GitHub Actions)

```
push to main/develop
        │
        ├── lint (Ruff + Black)
        ├── test (91 tests, SQLite in-memory + Redis service)
        ├── security (Bandit SAST scan)
        ├── build (Docker multi-stage build → GHCR)
        └── deploy (SSH → docker compose pull + up + alembic migrate)
```

Required GitHub Secrets:
- `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`
- `DEPLOY_PORT` (default: 22)

---

## Monitoring

### Prometheus Metrics (GET /metrics)
- `http_requests_total` — Request counter
- `http_errors_total` — 4xx/5xx counter
- `http_request_duration_ms_sum` — Latency accumulator
- `active_connections` — Real-time connection gauge
- `cache_hits_total` / `cache_misses_total` — Cache efficiency
- `db_queries_total` — Database query counter

### Grafana Dashboards
Prometheus data source auto-provisioned from `grafana/provisioning/`.

### OpenTelemetry
Set `OTEL_ENDPOINT=http://otel-collector:4317` to enable distributed tracing.

---

## Project Structure

```
GITAM CareerHub/
├── backend/
│   ├── app/
│   │   ├── ai/              # LLM providers, RAG, prompt engine
│   │   ├── api/v1/
│   │   │   └── endpoints/   # 15 router modules
│   │   ├── core/            # config, security, logging, redis, metrics, feature_flags, celery
│   │   ├── database/        # session (pooling), base, init_db, seeds
│   │   ├── dependencies/    # FastAPI Depends (auth, db)
│   │   ├── middleware/       # cors, rate_limit, rbac, security_headers, request_logging
│   │   ├── models/          # 50+ SQLAlchemy models across 12 modules
│   │   ├── schemas/         # Pydantic v2 schemas
│   │   └── services/        # 12 service layer modules
│   ├── alembic/             # Database migrations
│   ├── scripts/             # db_backup.sh, seed scripts
│   ├── tests/               # 91 tests across 8 suites + load test
│   ├── Dockerfile           # Multi-stage production build
│   ├── requirements.txt     # Production dependencies
│   └── .env.example         # Environment template
├── nginx/nginx.conf          # Reverse proxy (TLS, gzip, rate limit, SSE)
├── prometheus/prometheus.yml # Metrics scraping config
├── docker-compose.yml        # Production stack (8 services)
├── docker-compose.override.yml  # Local dev hot-reload override
└── .github/workflows/ci-cd.yml  # GitHub Actions CI/CD pipeline
```
