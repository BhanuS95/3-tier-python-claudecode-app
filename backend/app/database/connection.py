"""
Database connection layer.

Exposes a single SQLAlchemy `db` instance and `migrate` (Flask-Migrate)
instance that are initialized against the Flask app in app/__init__.py.
All models import `db` from here rather than creating their own engine.
"""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


def check_database_connection() -> bool:
    """
    Lightweight connectivity check used by the readiness probe.
    Returns True if a trivial query succeeds, False otherwise.
    """
    from sqlalchemy import text

    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception:  # readiness probe must not raise on connectivity failure
        return False
