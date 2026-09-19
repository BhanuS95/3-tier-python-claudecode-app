# DevOps Handover Document

This document contains everything a DevOps engineer needs to
containerize, secure, deploy, monitor, and expose this application in
production, without needing to ask the development team any of the
questions listed in the root `README.md`'s design goals. If anything
here is unclear or missing, please treat that as a documentation bug
and flag it -- it should not require re-reading the source code.

---

## 1. Application Information

| Field               | Value                                   |
|----------------------|--------------------------------------------|
| Application name       | task-management-app                           |
| Application version      | 1.0.0                                            |
| Application owner          | Backend/Platform team (update with real owner)   |
| Repository                    | `<insert git remote URL>`                            |
| Branch                          | `main`                                                 |
| Programming language              | Python 3.12                                              |
| Framework                            | Flask 3.0 (backend), static HTML/CSS/JS (frontend)          |

## 2. Runtime Information

### Backend

| Field              | Value                                                                 |
|---------------------|--------------------------------------------------------------------------|
| Python version         | 3.12                                                                        |
| Application port          | `5000` (configurable via `APP_PORT`)                                          |
| Production server            | Gunicorn 22 (WSGI)                                                               |
| Startup command                 | `gunicorn --bind 0.0.0.0:${APP_PORT:-5000} --workers ${GUNICORN_WORKERS:-4} --graceful-timeout 30 --timeout 60 --access-logfile - --error-logfile - wsgi:app` |
| Working directory                  | `/app` (inside the container)                                                       |
| Entrypoint module                     | `wsgi.py` -> exposes `app` (Flask instance from `app.create_app()`)                    |

### Frontend

| Field              | Value                                          |
|---------------------|----------------------------------------------------|
| Server                 | Nginx 1.27 (alpine)                                    |
| Port                     | `3000`                                                    |
| Content                    | Static files only (`index.html`, `css/`, `js/`)               |
| Reverse proxy                 | Proxies `/api/*` and `/health/*` to the backend service (`http://backend:5000`) -- see `frontend/nginx.conf` |

## 3. Dependencies

| Dependency    | Required? | Notes                                                      |
|----------------|-----------|----------------------------------------------------------------|
| PostgreSQL 16    | Yes       | Primary data store. See §9 (Database Migration Strategy) and `database/README.md` for schema/permissions |
| Redis              | No        | Not used by this application                                        |
| External APIs        | No        | The application makes no outbound calls to third-party services         |
| Third-party services     | No        | None                                                                        |

## 4. Environment Variables

**All configuration is environment-variable-driven. Nothing is
hard-coded. No `.env` file is ever baked into a container image.**

| Variable              | Required | Sensitive | Example                    | Description                                             |
|------------------------|----------|-----------|-------------------------------|-------------------------------------------------------------|
| `APP_ENV`                | Yes      | No        | `production`                     | `development` \| `testing` \| `production`                     |
| `APP_PORT`                 | Yes      | No        | `5000`                             | Port the backend listens on inside the container                 |
| `APP_DEBUG`                  | Yes      | No        | `false`                              | **Must** be `false` in production                                   |
| `LOG_LEVEL`                    | No       | No        | `INFO`                                  | `DEBUG`\|`INFO`\|`WARNING`\|`ERROR`\|`CRITICAL`                       |
| `SECRET_KEY`                     | Yes      | **Yes**   | `<random 64-char hex>`                    | Flask signing key. Generate with `python -c "import secrets;print(secrets.token_hex(32))"`. Inject via secrets manager. |
| `GUNICORN_WORKERS`                 | No       | No        | `4`                                          | Tune to `(2 x vCPU) + 1` as a starting point                          |
| `DATABASE_HOST`                       | Yes      | No        | `postgres.internal`                             | PostgreSQL hostname                                                       |
| `DATABASE_PORT`                         | Yes      | No        | `5432`                                             | PostgreSQL port                                                              |
| `DATABASE_NAME`                           | Yes      | No        | `taskdb`                                              | Database name                                                                  |
| `DATABASE_USER`                             | Yes      | **Yes**   | `taskuser`                                              | Database user                                                                    |
| `DATABASE_PASSWORD`                           | Yes      | **Yes**   | `<from secrets manager>`                                  | Database password -- never in plain env vars in source control or CI logs           |
| `DATABASE_POOL_SIZE`                            | No       | No        | `5`                                                          | SQLAlchemy pool size                                                                   |
| `DATABASE_MAX_OVERFLOW`                           | No       | No        | `10`                                                            | SQLAlchemy max overflow connections                                                       |
| `CORS_ORIGINS`                                      | Yes      | No        | `https://tasks.example.com`                                        | **Must** be an explicit origin (or comma-separated list) in production, never `*`             |

Never provide real production secrets in this document, in the
repository, or in CI logs -- the examples above are placeholders only.

## 5. What DevOps Needs to Create / Provision

The application image and code are complete and require no changes to
be containerized. DevOps still needs to provide:

- Container image build/push pipeline (registry, see §7)
- Environment variables (ConfigMap-equivalent, non-sensitive values from §4)
- Secrets (Secret-equivalent: `SECRET_KEY`, `DATABASE_PASSWORD`, `DATABASE_USER` if treated as sensitive)
- PostgreSQL 16 instance (managed service recommended, or a StatefulSet with persistent storage)
- Persistent storage for PostgreSQL data
- Ingress / load balancer with TLS termination in front of the frontend (and backend, if the backend is reached directly)
- DNS records pointing at the ingress/load balancer
- TLS certificate (managed cert / ACME, e.g. via cert-manager)
- Health probes wired to `/health/live` and `/health/ready` (see §8)
- Resource requests/limits (see §8 for starting values)
- Horizontal scaling policy if traffic warrants it (the backend is stateless and safely horizontally scalable; the frontend is static and trivially scalable)
- Centralized logging pipeline (the app already writes structured logs to stdout/stderr -- see §10)
- Monitoring/alerting on the health endpoints and standard container metrics (CPU, memory, restart count)

## 6. Developer vs. DevOps Responsibility

| Developer Responsibility           | DevOps Responsibility                    |
|--------------------------------------|-----------------------------------------------|
| Application code                        | CI/CD pipeline orchestration                       |
| Dockerfile (backend + frontend)            | Container registry                                    |
| API documentation                            | Kubernetes cluster / hosting platform                     |
| Database migrations (Alembic)                   | Infrastructure (networking, VPC, subnets)                   |
| Health endpoints                                   | Secrets management (Vault, AWS/GCP/Azure secrets manager)      |
| Application configuration (env var wiring)            | Ingress / load balancer / TLS                                     |
| Automated tests                                         | Monitoring and alerting                                              |
| Application dependencies (`requirements*.txt`)             | Log aggregation                                                          |
|                                                                | Autoscaling policy                                                          |
|                                                                | Backup and disaster recovery for PostgreSQL                                   |

## 7. Container Image Information

| Item                  | Backend                                | Frontend                              |
|------------------------|-------------------------------------------|--------------------------------------------|
| Expected image name       | `three-tier-python-backend`                    | `three-tier-python-frontend`                      |
| Container port               | `5000`                                             | `3000`                                                 |
| Startup command                  | See §2 (baked into the image's `CMD`)                   | `nginx -g "daemon off;"` (baked into the image's `CMD`) |
| Health endpoint                     | `GET /health/live`                                          | `GET /` (static file existence)                              |
| Readiness endpoint                     | `GET /health/ready`                                              | N/A (stateless static content; liveness is sufficient)             |
| Required env vars                         | See §4                                                                 | None required at build or run time (`API_BASE_URL` is compiled into the static JS at authoring time, not injected at runtime) |
| Runs as                                      | Non-root user `appuser` (UID 1000)                                        | Nginx's built-in unprivileged worker processes                        |
| Base image                                      | `python:3.12-slim`                                                            | `nginx:1.27-alpine`                                                       |

Build commands (from repository root):

```bash
docker build -t <registry>/three-tier-python-backend:<tag> ./backend
docker build -t <registry>/three-tier-python-frontend:<tag> ./frontend
```

## 8. Kubernetes Readiness

Kubernetes manifests are intentionally **not** included in this
repository (per design scope) -- the information below is everything
needed to author them.

| Item                    | Backend                                       | Frontend            |
|---------------------------|----------------------------------------------------|--------------------------|
| Container port                | `5000`                                                  | `3000`                       |
| Liveness probe                    | `GET /health/live`, e.g. `initialDelaySeconds: 10, periodSeconds: 15, failureThreshold: 3` | `GET /`, same defaults      |
| Readiness probe                      | `GET /health/ready`, e.g. `initialDelaySeconds: 5, periodSeconds: 10, failureThreshold: 3` | `GET /`, same defaults          |
| Environment variables                    | See §4 (non-sensitive as ConfigMap, sensitive as Secret) | None required                       |
| Secrets                                     | `SECRET_KEY`, `DATABASE_PASSWORD` (and `DATABASE_USER` if treated as sensitive) | None                                     |
| ConfigMaps                                     | `APP_ENV`, `APP_PORT`, `LOG_LEVEL`, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `CORS_ORIGINS` | None                                        |
| Suggested CPU request                             | `100m`                                                        | `50m`                                                            |
| Suggested memory request                             | `128Mi`                                                        | `32Mi`                                                              |
| Suggested CPU limit                                     | `500m`                                                            | `100m`                                                                 |
| Suggested memory limit                                     | `256Mi`                                                            | `64Mi`                                                                    |
| Suggested replicas                                            | `2+` (stateless; safe to scale horizontally)                          | `2+` (stateless static content)                                              |
| Graceful shutdown behavior                                       | See §11                                                                    | Nginx handles SIGTERM by completing in-flight requests, then exiting; no custom handling needed |

Tune CPU/memory requests and limits against real load-test results
before finalizing production sizing -- the values above are
conservative starting points, not guarantees.

## 9. Database Migration Strategy

Migrations are managed with **Alembic** (via Flask-Migrate) and live
in `backend/migrations/versions/`. There is exactly one migration
today: `0001_create_tasks_table.py`.

| Scenario           | Command                                    |
|----------------------|--------------------------------------------|
| Initial migration       | `flask db upgrade` (applies all migrations from scratch on an empty database) |
| New migration               | `flask db migrate -m "description"` then review the generated file before committing |
| Apply pending migrations         | `flask db upgrade`                                                                   |
| Rollback one revision                | `flask db downgrade -1`                                                                  |
| Verify current state                    | `flask db current` (applied revision) and `flask db history` (full lineage)                  |

**Recommendation: run migrations as an explicit deployment step, not
automatically embedded in every container start in production.**

This repository's `docker-compose.yml` runs `flask db upgrade` before
starting Gunicorn -- that is intentional and appropriate for local/dev
Compose environments, where simplicity matters more than deployment
choreography. For production Kubernetes deployments, DevOps should
instead:

- Run migrations as a **Kubernetes `Job`** (using the same backend
  image, overriding the command to `flask db upgrade`) as a pre-deploy
  step in the CI/CD pipeline, before rolling out the new Deployment.
- This avoids every replica racing to run migrations concurrently on
  startup, and lets the pipeline fail fast (and block the rollout) if
  a migration fails, rather than surfacing as pod crash loops.
- Never run `flask db upgrade` automatically inside each pod's
  container startup command for production/Kubernetes -- that pattern
  is only acceptable for single-instance local Compose environments,
  exactly as this project already scopes it.

## 10. Logging

The application logs exclusively to **stdout/stderr** in a structured,
single-line format:

```
2026-09-19T10:00:00 | INFO     | task-management-api | app.services.task_service | Task created id=...
```

Fields: timestamp, level, application name, logger/module name,
message. No log file is written inside the container, so no volume is
needed for logs -- the container runtime (Docker/Kubernetes) is
expected to capture stdout/stderr and forward it to whatever log
aggregation system is in use (e.g. Fluent Bit -> Elasticsearch/Loki/
CloudWatch/Datadog).

Log level is controlled via `LOG_LEVEL` (default `INFO` in
production). The application **never logs** passwords, database
credentials, API keys, tokens, or other secrets.

## 11. Graceful Shutdown

- Docker/Kubernetes send **`SIGTERM`** to the container's main process
  on `docker stop`, pod termination, or a rolling update.
- Gunicorn (the backend's production server) handles `SIGTERM` by
  entering graceful shutdown: it stops accepting new connections and
  allows in-flight requests to finish, up to `--graceful-timeout 30`
  seconds (configured in the Dockerfile `CMD` / Compose `command`),
  before workers exit.
- If workers haven't exited by the time Kubernetes' own
  `terminationGracePeriodSeconds` elapses (Kubernetes default: 30s;
  recommend setting this to at least `35`-`40` to exceed Gunicorn's own
  graceful-timeout), Kubernetes sends **`SIGKILL`** to force-stop the
  process.
- No custom signal-handling code is required in the application itself
  -- Gunicorn's built-in behavior covers this. DevOps should simply
  ensure `terminationGracePeriodSeconds` in the pod spec is greater
  than Gunicorn's `--graceful-timeout` value.
- Nginx (frontend) similarly completes in-flight requests on `SIGTERM`
  and requires no special configuration.

## 12. Production Configuration Checklist

```
[x] Secrets externalized (SECRET_KEY, DATABASE_PASSWORD via env vars)
[x] Database credentials externalized
[x] Debug disabled by default outside development (APP_DEBUG must be set false in prod)
[x] Production server configured (Gunicorn, not the Flask dev server)
[x] Logging configured (structured, stdout/stderr)
[x] Health (liveness) endpoint implemented (/health/live)
[x] Readiness endpoint implemented (/health/ready, checks PostgreSQL)
[x] Database migrations implemented (Alembic, backend/migrations/)
[x] Tests implemented (17 tests, 92% coverage, pytest + pytest-cov)
[x] Dockerfile created (backend and frontend)
[x] Non-root container user (backend: appuser; frontend: nginx's own unprivileged workers)
[x] Docker image builds successfully (verified during development)
[x] Docker Compose tested (backend, frontend, postgres wired with healthchecks)
[x] Dependencies pinned (requirements.txt / requirements-dev.txt)
[x] Security scan possible (standard pip/Docker images; no exotic dependencies blocking scanners)
[x] CI/CD compatible (lint/test/build stages need nothing beyond what's in this repo)
[x] Kubernetes deployment requirements documented (this document, §8)
[ ] Authentication/authorization -- NOT implemented in this reference app; add before any
    public-facing production deployment that isn't behind a trusted network boundary
[ ] TLS certificate, ingress, DNS -- to be provisioned by DevOps per §5
[ ] Secrets manager integration -- to be provisioned by DevOps per §5
[ ] Managed PostgreSQL with backups/PITR -- to be provisioned by DevOps per §5
```

## 13. Open Items for DevOps to Decide

These are intentionally left to the deploying organization's existing
standards rather than prescribed here:

- Which container registry (ECR/GCR/ACR/Harbor/etc.)
- Which secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager, etc.)
- Which log aggregation and monitoring stack
- Whether the backend is reachable directly (own ingress path) or only
  via the frontend's Nginx proxy (§7 frontend "reverse proxy" note)
- Authentication/authorization approach, if/when this moves beyond an
  internal or trusted-network deployment
