# Three-Tier Task Management Application

A production-ready, three-tier Python web application: a static
HTML/CSS/JS frontend, a Flask REST API backend, and a PostgreSQL
database, built to be handed off to a DevOps team for containerized
deployment with **no clarification needed** (see
`docs/DEVOPS_HANDOVER.md`).

## 1. Project Overview

This is a Task Management application demonstrating complete CRUD
functionality across a real three-tier architecture:

```
Frontend (HTML/CSS/JS)  -->  Backend REST API (Flask)  -->  PostgreSQL
```

Users can create, view, update, delete, and mark tasks as completed
entirely through the UI, which talks to the backend exclusively over
REST.

## 2. Architecture

```
                   ┌───────────────┐
                   │     User      │
                   └───────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
                   │   Frontend    │
                   │ HTML/CSS/JS   │
                   │   (Nginx)     │
                   └───────┬───────┘
                           │ REST API (JSON over HTTP)
                           ▼
                   ┌───────────────┐
                   │    Backend    │
                   │  Flask + REST │
                   │   (Gunicorn)  │
                   └───────┬───────┘
                           │ SQLAlchemy / psycopg2
                           ▼
                   ┌───────────────┐
                   │  PostgreSQL   │
                   │   Database    │
                   └───────────────┘
```

**How this maps to a production deployment:**

```
Internet
   │
   ▼
Load Balancer / Ingress (TLS termination)
   │
   ├──► Frontend Service  (Nginx pods, static assets)
   │
   └──► Backend Service   (Gunicorn pods, /api and /health)
              │
              ▼
        PostgreSQL (managed service or StatefulSet, private subnet/network)
```

The backend and frontend are independently containerized, independently
scalable, and communicate only via REST/HTTP. PostgreSQL is never
exposed to the public internet.

## 3. Technology Stack

| Layer      | Technology                                              |
|------------|-----------------------------------------------------------|
| Frontend   | HTML5, CSS3, vanilla JavaScript (fetch API), Nginx (serving) |
| Backend    | Python 3.12, Flask 3.0, Gunicorn 22 (production WSGI server) |
| Validation | Marshmallow 3.21                                            |
| ORM        | SQLAlchemy 2.0 (via Flask-SQLAlchemy 3.1)                    |
| Migrations | Alembic 1.13 (via Flask-Migrate 4.0)                          |
| Database   | PostgreSQL 16                                                 |
| Driver     | psycopg2-binary 2.9                                            |
| Testing    | pytest 8.2, pytest-cov 5.0                                       |
| Linting    | ruff 0.5, black 24.4                                              |
| Containers | Docker, Docker Compose                                             |

Exact pinned versions are in `backend/requirements.txt` and
`backend/requirements-dev.txt`.

## 4. Project Structure

```
three-tier-python-app/
│
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   ├── js/app.js
│   ├── nginx.conf
│   ├── Dockerfile
│   ├── .dockerignore
│   └── README.md
│
├── backend/
│   ├── app/
│   │   ├── __init__.py           # App factory, logging, error handlers
│   │   ├── config.py              # Environment-variable configuration
│   │   ├── routes/task_routes.py   # HTTP endpoints
│   │   ├── models/task.py           # SQLAlchemy model
│   │   ├── services/task_service.py  # Business logic
│   │   ├── schemas/task_schema.py     # Marshmallow validation
│   │   ├── database/connection.py      # db/migrate instances
│   │   ├── health/health_routes.py      # /health/live, /health/ready
│   │   └── utils/exceptions.py            # Shared app exceptions
│   ├── migrations/                 # Alembic environment + versions/0001_...
│   ├── tests/                       # pytest suite (17 tests, 92% coverage)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── pyproject.toml               # ruff + black config
│   ├── wsgi.py                       # Production entrypoint
│   ├── run.py                         # Local dev entrypoint
│   ├── .env.example
│   ├── Dockerfile
│   ├── .dockerignore
│   └── README.md
│
├── database/
│   ├── init/README.md
│   └── README.md                    # Schema, users, permissions
│
├── docs/
│   └── DEVOPS_HANDOVER.md            # Full developer-to-DevOps handover
│
├── docker-compose.yml
├── .gitignore
├── .env.example
├── README.md                         # (this file)
└── LICENSE
```

## 5. Prerequisites

For local (non-Docker) development:

```
Git
Python 3.12+
pip
PostgreSQL 16 (running locally or reachable)
```

For containerized development:

```
Docker
Docker Compose (v2, i.e. `docker compose`, not the old `docker-compose`)
```

Verify your tooling:

```bash
python3 --version
pip --version
git --version
docker --version
docker compose version
```

## 6. Local Developer Setup (without Docker)

```bash
git clone <repository-url>
cd three-tier-python-app

# 1. Backend: virtual environment + dependencies
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r backend/requirements-dev.txt

# 2. Configure environment
cp backend/.env.example backend/.env
# edit backend/.env if your local PostgreSQL differs from the defaults

# 3. Make sure PostgreSQL is running and the database/user exist, e.g.:
#    psql -U postgres -c "CREATE DATABASE taskdb;"
#    psql -U postgres -c "CREATE USER taskuser WITH PASSWORD 'changeme';"
#    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE taskdb TO taskuser;"

# 4. Run database migrations
cd backend
flask db upgrade
cd ..

# 5. Start the backend (development server)
cd backend
python run.py
# Backend now running at http://localhost:5000
cd ..

# 6. In a second terminal, start the frontend
cd frontend
python3 -m http.server 3000
# Frontend now running at http://localhost:3000
```

Open your browser at:

- **Frontend:** http://localhost:3000
- **Backend root API:** http://localhost:5000/api/tasks
- **Health checks:** http://localhost:5000/health/live , http://localhost:5000/health/ready

## 7. Environment Variables

Root `.env.example` (used by Docker Compose) and `backend/.env.example`
(used for bare-metal backend runs) document every variable. Summary:

| Variable              | Required | Sensitive | Default (dev)          | Description                                    |
|------------------------|----------|-----------|--------------------------|--------------------------------------------------|
| `APP_ENV`               | No       | No        | `development`             | `development` \| `testing` \| `production`         |
| `APP_PORT`               | No       | No        | `5000`                     | Port the backend listens on                          |
| `APP_DEBUG`               | No       | No        | `true` (dev only)            | Must be `false`/unset in production                    |
| `LOG_LEVEL`                | No       | No        | `DEBUG`                       | `DEBUG`\|`INFO`\|`WARNING`\|`ERROR`\|`CRITICAL`          |
| `SECRET_KEY`                | Yes      | **Yes**   | `change-me`                     | Flask signing key -- must be a strong random value in prod |
| `GUNICORN_WORKERS`           | No       | No        | `4`                               | Gunicorn worker process count                              |
| `DATABASE_HOST`               | Yes      | No        | `postgres` (compose) / `localhost` | PostgreSQL hostname                                        |
| `DATABASE_PORT`                | Yes      | No        | `5432`                               | PostgreSQL port                                             |
| `DATABASE_NAME`                  | Yes      | No        | `taskdb`                               | Database name                                                |
| `DATABASE_USER`                   | Yes      | **Yes**   | `taskuser`                               | Database user                                                |
| `DATABASE_PASSWORD`                | Yes      | **Yes**   | `changeme`                                 | Database password                                            |
| `DATABASE_POOL_SIZE`                 | No       | No        | `5`                                           | SQLAlchemy connection pool size                                |
| `DATABASE_MAX_OVERFLOW`               | No       | No        | `10`                                            | SQLAlchemy max overflow connections                             |
| `CORS_ORIGINS`                          | No       | No        | `*` (dev) / explicit origin (prod) | Allowed CORS origins for `/api/*`                                |
| `API_BASE_URL`                            | No       | No        | `http://localhost:5000`               | Frontend-only: where the JS should call the API                    |

**Never commit a real `.env` file.** `.gitignore` excludes it; only
`.env.example` files are tracked.

## 8. Database Setup

See `database/README.md` for the full schema (tables, columns, types,
constraints, indexes) and required PostgreSQL user permissions.

Migrations are managed with Alembic via Flask-Migrate, from `backend/`:

```bash
flask db upgrade          # apply all pending migrations (idempotent)
flask db downgrade -1      # roll back one revision
flask db migrate -m "..."   # generate a new migration after model changes
flask db current             # show the currently applied revision
flask db history               # show migration history
```

The application never auto-runs migrations on request handling, and it
does not depend on manually-run SQL. See
`docs/DEVOPS_HANDOVER.md` → "Database Migration Strategy" for exactly
when/how migrations should run in each environment.

## 9. API Documentation

Base path: `/api/tasks`. All request/response bodies are JSON.

| Method | Endpoint                     | Purpose                     |
|--------|-------------------------------|-------------------------------|
| GET    | `/api/tasks`                    | Get all tasks (optional `?status=pending\|in_progress\|completed`) |
| GET    | `/api/tasks/{id}`                 | Get a single task              |
| POST   | `/api/tasks`                       | Create a task                    |
| PUT    | `/api/tasks/{id}`                    | Update a task                      |
| DELETE | `/api/tasks/{id}`                      | Delete a task                        |
| PATCH  | `/api/tasks/{id}/complete`               | Mark a task as completed               |
| GET    | `/health/live`                             | Liveness probe                           |
| GET    | `/health/ready`                             | Readiness probe (checks PostgreSQL)        |

Authentication: **none** in this reference implementation (no
`Authorization` header required). See "Security" (§14) for how to add
it before exposing this publicly.

### GET /api/tasks

```bash
curl http://localhost:5000/api/tasks
curl "http://localhost:5000/api/tasks?status=completed"
```

Response `200 OK`:
```json
[
  {
    "id": "3fae6f2e-2222-4f8a-9a1a-000000000001",
    "title": "Write docs",
    "description": "Add API examples",
    "status": "pending",
    "completed": false,
    "created_at": "2026-09-19T10:00:00+00:00",
    "updated_at": "2026-09-19T10:00:00+00:00"
  }
]
```

### GET /api/tasks/{id}

```bash
curl http://localhost:5000/api/tasks/3fae6f2e-2222-4f8a-9a1a-000000000001
```

Response `200 OK`: single task object (as above).
Response `404 Not Found`:
```json
{ "error": { "code": "TASK_NOT_FOUND", "message": "Task '...' was not found." } }
```

### POST /api/tasks

```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Write docs", "description": "Add API examples"}'
```

Request body:
| Field         | Type   | Required | Notes                                      |
|---------------|--------|----------|----------------------------------------------|
| `title`         | string | Yes      | 1–255 characters                                |
| `description`     | string | No       | Nullable                                          |
| `status`            | string | No       | `pending` (default) \| `in_progress` \| `completed` |

Response `201 Created`: the created task.
Response `422 Unprocessable Entity` on invalid payload:
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "title: Missing data for required field." } }
```

### PUT /api/tasks/{id}

```bash
curl -X PUT http://localhost:5000/api/tasks/3fae6f2e-2222-4f8a-9a1a-000000000001 \
  -H "Content-Type: application/json" \
  -d '{"title": "Write docs v2", "status": "in_progress"}'
```

All fields optional; only supplied fields are updated. Response `200 OK`
(updated task), `404` if not found, `422` on invalid values.

### DELETE /api/tasks/{id}

```bash
curl -X DELETE http://localhost:5000/api/tasks/3fae6f2e-2222-4f8a-9a1a-000000000001
```

Response `204 No Content` on success, `404` if not found.

### PATCH /api/tasks/{id}/complete

```bash
curl -X PATCH http://localhost:5000/api/tasks/3fae6f2e-2222-4f8a-9a1a-000000000001/complete
```

Response `200 OK`: the task with `status: "completed"`.

### Error response format (all endpoints)

```json
{ "error": { "code": "TASK_NOT_FOUND", "message": "Task was not found" } }
```

| Status | Meaning                                              |
|--------|---------------------------------------------------------|
| 200    | Successful request                                         |
| 201    | Resource created                                              |
| 204    | Successful request, no body (delete)                            |
| 400    | Bad request                                                        |
| 404    | Resource not found                                                    |
| 409    | Conflict                                                                  |
| 422    | Validation error                                                            |
| 500    | Internal server error (details never leaked to the client; logged server-side) |
| 503    | Dependency unavailable (readiness probe only)                                    |

## 10. Testing

From `backend/`, with `requirements-dev.txt` installed:

```bash
pytest
pytest --cov=app --cov-report=term-missing
```

Expected result: **17 passed**, coverage ≈ **92%**. Tests cover the API
layer (all CRUD verbs, validation failures, not-found scenarios) and
the service layer directly, using an in-memory SQLite database so no
external services are required.

## 11. Docker

Build and run the backend image standalone:

```bash
cd backend
docker build -t three-tier-python-backend:latest .
docker run --rm -p 5000:5000 \
  -e DATABASE_HOST=host.docker.internal \
  -e DATABASE_PASSWORD=changeme \
  -e SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_hex(32))") \
  three-tier-python-backend:latest
```

Build the frontend image standalone:

```bash
cd frontend
docker build -t three-tier-python-frontend:latest .
docker run --rm -p 3000:3000 three-tier-python-frontend:latest
```

## 12. Docker Compose (full stack)

From the repository root:

```bash
cp .env.example .env    # edit values as needed
docker compose up --build
```

This starts, in dependency order (via `depends_on` + healthchecks):

1. `postgres` -- PostgreSQL 16, persistent named volume `postgres_data`, **not** exposed to the host by default
2. `backend` -- runs `flask db upgrade` then starts Gunicorn, exposed on `${APP_PORT:-5000}`
3. `frontend` -- Nginx serving the static site, exposed on `3000`, proxies `/api/*` and `/health/*` to `backend`

Then open:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api/tasks
- Health: http://localhost:5000/health/live

Tear down:

```bash
docker compose down          # stop and remove containers
docker compose down -v        # also remove the postgres_data volume (destroys data)
```

## 13. Health Checks

- **`GET /health/live`** -- Liveness. Confirms the Python process is up and
  able to respond. Does **not** check the database. If this fails,
  the orchestrator should **restart** the container/pod.
- **`GET /health/ready`** -- Readiness. Confirms the app can serve real
  traffic by checking PostgreSQL connectivity. If this fails, the
  orchestrator should **remove the instance from load-balancer
  rotation** without restarting it (the process may still be fine;
  the dependency isn't).

```json
// GET /health/live -> 200
{ "status": "UP" }

// GET /health/ready -> 200 (or 503 if the DB is unreachable)
{ "status": "UP", "database": "UP" }
```

## 14. Security

- Non-root container users in both the backend and frontend images
- All secrets/config via environment variables -- nothing hard-coded, `.env` never committed or copied into images
- Marshmallow validates every request payload before it reaches business logic
- SQL injection protection via the SQLAlchemy ORM (parameterized queries throughout; no raw string-built SQL)
- Centralized error handling -- stack traces and internals are never returned to clients, only logged server-side
- Pinned dependency versions in `requirements.txt` / `requirements-dev.txt`
- CORS restricted via `CORS_ORIGINS` (must be set to explicit origins in production, not `*`)
- Basic security headers set by the frontend's Nginx (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`)
- PostgreSQL is not exposed to the host/internet in `docker-compose.yml`
- `.gitignore` / `.dockerignore` exclude `.env`, virtual environments, caches, and test artifacts

This reference implementation does not include authentication/
authorization (no login system) -- see `docs/DEVOPS_HANDOVER.md` for
notes on adding it before any public deployment.

## 15. CI/CD Readiness

Recommended pipeline stages (works with Jenkins, GitHub Actions, GitLab
CI, or any similar system):

```
Checkout
   ↓
Install Dependencies   (pip install -r backend/requirements-dev.txt)
   ↓
Lint                     (ruff check ., black --check .)
   ↓
Unit Tests                 (pytest --cov=app)
   ↓
Security Scan                 (e.g. pip-audit / Trivy / Snyk -- not bundled; DevOps choice)
   ↓
Docker Build                     (docker build backend/, frontend/)
   ↓
Container Scan                     (e.g. Trivy / Grype -- DevOps choice)
   ↓
Push Image                           (to the chosen container registry)
   ↓
Deploy                                 (to the target environment)
   ↓
Smoke Test                               (curl /health/live, /health/ready)
```

Everything left of "Docker Build" needs nothing beyond what's already
in this repository. See `docs/DEVOPS_HANDOVER.md` for what DevOps must
still provide (registry, cluster, secrets manager, etc.).

## 16. DevOps Handover

The complete developer-to-DevOps handover document, including runtime
information, the full environment variable table, container image
details, migration strategy, graceful shutdown behavior, Kubernetes
readiness information, and a production configuration checklist, is
at:

**[`docs/DEVOPS_HANDOVER.md`](docs/DEVOPS_HANDOVER.md)**

## 17. Production Considerations

Before deploying this to production, DevOps/platform teams should, at minimum:
- Provision managed or replicated PostgreSQL with backups and point-in-time recovery
- Inject `SECRET_KEY` and `DATABASE_PASSWORD` from a secrets manager (never plain env vars in source control or CI logs)
- Set `APP_ENV=production`, `APP_DEBUG=false`, and an explicit `CORS_ORIGINS`
- Terminate TLS at a load balancer / ingress in front of both frontend and backend
- Configure autoscaling, resource requests/limits, and multiple replicas (see `docs/DEVOPS_HANDOVER.md` → Kubernetes Readiness)
- Ship container logs (stdout/stderr) to a central logging system
- Add authentication/authorization if this API will be reachable outside a trusted network

See §14 (Security) and `docs/DEVOPS_HANDOVER.md` for the complete list.

## 18. Troubleshooting

| Problem | Possible cause | How to verify | How to fix |
|---|---|---|---|
| `psycopg2.OperationalError: could not connect to server` | PostgreSQL not running / wrong host / wrong port | `pg_isready -h $DATABASE_HOST -p $DATABASE_PORT` | Start PostgreSQL; confirm `DATABASE_HOST`/`DATABASE_PORT` match where it's actually listening (`postgres` inside Compose, `localhost` when run bare-metal) |
| `Address already in use` on port 5000/3000 | Another process already bound to the port | `lsof -i :5000` (macOS/Linux) or `netstat -ano \| findstr 5000` (Windows) | Stop the other process, or change `APP_PORT` / the Compose port mapping |
| `password authentication failed for user "taskuser"` | Wrong password, or user/database not yet created | `psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME` | Ensure `DATABASE_PASSWORD` matches what PostgreSQL was initialized with; recreate the user/database if needed |
| App crashes on startup citing a missing env var / wrong DB URL | `.env` not created, or a required variable unset | `env \| grep DATABASE_` inside the container/shell | `cp backend/.env.example backend/.env` (or root `.env.example` for Compose) and fill in real values |
| `alembic.util.exc.CommandError` / migration failure | Migrations out of sync with the actual DB schema, or DB unreachable during migration | `flask db current` vs `flask db history` | Fix connectivity first; if history has diverged, coordinate a `flask db stamp <revision>` with whoever owns that environment -- never do this blindly in production |
| `pip install` fails on `psycopg2-binary` | Missing system libraries (rare, mostly only affects building from source, not the `-binary` wheel) | Re-run with `-v` to see the actual error | Ensure you're using `psycopg2-binary` (already pinned in `requirements.txt`), not `psycopg2`; on Debian/Ubuntu base images `libpq5` covers the runtime `.so` |
| `docker build` fails | Network restrictions, base image pull failure, or a `COPY` path typo | Re-run `docker build` with `--progress=plain` | Check registry connectivity; confirm you're building from the correct context (`backend/` or `frontend/`, not the repo root) |
| Backend container can't reach PostgreSQL in Compose | `DATABASE_HOST` set to `localhost` instead of the service name `postgres` | `docker compose logs backend` | Set `DATABASE_HOST=postgres` (the Compose service name is the hostname on the internal network) |
| Frontend can't reach the backend (network errors in browser console) | `API_BASE_URL` pointing at the wrong host/port, or backend not yet healthy | Open browser DevTools → Network tab; check the failing request's URL | Confirm the backend is up (`curl http://localhost:5000/health/live`) and `API_BASE_URL` in `frontend/js/app.js` matches where it's actually reachable |
| CORS error in the browser console | `CORS_ORIGINS` on the backend doesn't include the frontend's origin | Inspect the failing request/response headers in DevTools | Set `CORS_ORIGINS` to include the frontend's exact origin (scheme + host + port), or `*` for local development only |
| `/health/ready` returns `503` | PostgreSQL unreachable from the backend | `curl http://localhost:5000/health/ready`; check backend logs | Fix DB connectivity/credentials; this endpoint is designed to fail loudly rather than silently serve broken requests |

## License

MIT -- see `LICENSE`.
