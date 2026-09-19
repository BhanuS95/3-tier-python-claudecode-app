# Backend -- Task Management REST API

Python 3.12 / Flask 3 REST API backed by PostgreSQL via SQLAlchemy,
with Alembic migrations. See the root `README.md` for the full
project overview and `docs/DEVOPS_HANDOVER.md` for deployment details.

## Architecture

```
HTTP Request
     |
     v
Route / Controller   (app/routes)        <- Flask blueprints, HTTP only
     |
     v
Schema Validation     (app/schemas)      <- Marshmallow
     |
     v
Service Layer          (app/services)    <- business logic, no HTTP/Flask
     |
     v
Model / ORM            (app/models)      <- SQLAlchemy
     |
     v
PostgreSQL
```

## Directory structure

```
backend/
├── app/
│   ├── __init__.py         Application factory, logging, error handlers
│   ├── config.py            Environment-variable-driven configuration
│   ├── routes/               HTTP endpoints (blueprints)
│   ├── models/               SQLAlchemy models
│   ├── services/             Business logic
│   ├── schemas/               Marshmallow request/response validation
│   ├── database/              db/migrate instances, connectivity check
│   ├── health/                 Liveness/readiness endpoints
│   └── utils/                   Shared exceptions
├── migrations/                Alembic migration environment + versions
├── tests/                      pytest suite
├── requirements.txt            Runtime dependencies (pinned)
├── requirements-dev.txt        + test/lint tooling
├── wsgi.py                      Production entrypoint (gunicorn wsgi:app)
├── run.py                       Local dev entrypoint (python run.py)
├── Dockerfile
├── .dockerignore
└── .env.example
```

## Quick start (local, no Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # then start/point at a local PostgreSQL
flask db upgrade
python run.py
```

The API is then available at `http://localhost:5000/api/tasks`.

## Testing

```bash
pytest              # run the suite
pytest --cov=app --cov-report=term-missing   # with coverage
```

Tests run against an in-memory SQLite database (see `tests/conftest.py`)
so they require no external services and are safe to run anywhere,
including CI.

## Code quality

```bash
ruff check .
black --check .
```

## Production server

Never use `python run.py` / `flask run` in production. The image and
`docker-compose.yml` both start:

```bash
gunicorn --bind 0.0.0.0:$APP_PORT --workers $GUNICORN_WORKERS \
  --graceful-timeout 30 --timeout 60 --access-logfile - --error-logfile - wsgi:app
```

See `docs/DEVOPS_HANDOVER.md` for full runtime and deployment details.
