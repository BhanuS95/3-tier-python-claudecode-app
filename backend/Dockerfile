# ---------------------------------------------------------------------------
# Backend Dockerfile - Task Management API
#
# Base image   : python:3.12-slim (official, small attack surface)
# Working dir  : /app
# User         : non-root "appuser" (UID 1000)
# Port         : 5000 (overridable via APP_PORT at runtime)
# Entrypoint   : gunicorn serving wsgi:app
#
# This image intentionally does NOT copy .env or bake in any secret.
# All configuration is injected at container-run time via environment
# variables (see .env.example / docs/DEVOPS_HANDOVER.md).
# ---------------------------------------------------------------------------

FROM python:3.12-slim AS base

# Prevents Python from writing .pyc files and buffers stdout, which
# keeps container logs flowing immediately to stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_APP=wsgi.py

WORKDIR /app

# System dependencies required to build psycopg2 and provide healthcheck
# tooling (curl). Removed from the final layer's apt cache afterwards.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching: only
# reinstalled when requirements.txt actually changes).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source.
COPY app ./app
COPY migrations ./migrations
COPY wsgi.py run.py ./

# Create an unprivileged user and switch to it. The application never
# runs as root, in the container or otherwise.
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

# Documents the port the app listens on. Does not itself publish it;
# actual port mapping happens in docker-compose.yml / Kubernetes.
EXPOSE 5000

# Container-level health check (liveness). Kubernetes readers should
# still configure their own probes hitting /health/live and
# /health/ready directly (see docs/DEVOPS_HANDOVER.md).
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT:-5000}/health/live || exit 1

# Gunicorn: production WSGI server.
#   --workers 4          reasonable default for a small API; tune per CPU
#   --bind 0.0.0.0:$PORT binds to all interfaces inside the container
#   --graceful-timeout   allows in-flight requests to finish on SIGTERM
#   --access-logfile -   send access logs to stdout
#   --error-logfile  -   send error logs to stderr
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${APP_PORT:-5000} --workers ${GUNICORN_WORKERS:-4} --graceful-timeout 30 --timeout 60 --access-logfile - --error-logfile - wsgi:app"]
