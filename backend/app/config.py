"""
Centralized, environment-variable-driven configuration.

No secrets or environment-specific values are hard-coded here.
Everything is read from the process environment (populated via a
.env file locally, or via injected environment variables / secrets
in Docker / Kubernetes in production).
"""

import os

from dotenv import load_dotenv

# Loads a local .env file if present. In containers, real environment
# variables / mounted secrets take precedence and .env is not used.
load_dotenv()


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    """Shared configuration for all environments."""

    APP_ENV = os.getenv("APP_ENV", "development")
    APP_PORT = int(os.getenv("APP_PORT", "5000"))

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    # --- Database ---------------------------------------------------
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "taskdb")
    DATABASE_USER = os.getenv("DATABASE_USER", "taskuser")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "changeme")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection-pool tuning only applies to real server-based databases
    # (PostgreSQL). SQLite (used in tests) uses a StaticPool and does not
    # accept these keyword arguments.
    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {}
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,  # avoids stale-connection errors after DB restarts
            "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
        }

    # --- CORS ---------------------------------------------------------
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # --- Logging --------------------------------------------------------
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    DEBUG = False
    TESTING = False


class DevelopmentConfig(BaseConfig):
    DEBUG = _bool_env("APP_DEBUG", default=True)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    # Tests use a separate database (or sqlite in-memory) so they never
    # touch development/production data.
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    # SQLite (used by default in tests) does not support Postgres-style
    # connection pool sizing arguments.
    SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    """Return the config class for the current APP_ENV."""
    env = os.getenv("APP_ENV", "development").lower()
    return _CONFIG_MAP.get(env, DevelopmentConfig)
