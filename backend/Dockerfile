# =========================
# Stage 1: Build
# =========================
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt


# =========================
# Stage 2: Runtime
# =========================
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=5000

COPY --from=builder /install /usr/local

COPY . .

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=10s \
            --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('APP_PORT', '5000') + '/health/live', timeout=3)" || exit 1

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${APP_PORT:-5000} --workers ${GUNICORN_WORKERS:-4} --graceful-timeout 30 --timeout 60 --access-logfile - --error-logfile - wsgi:app"]
