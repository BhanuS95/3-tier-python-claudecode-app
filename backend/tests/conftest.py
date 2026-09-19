"""
Shared pytest fixtures.

Tests run against an in-memory SQLite database via TestingConfig so
they never touch a real PostgreSQL instance and can run anywhere
(including CI) with zero external dependencies.
"""

import os

os.environ.setdefault("APP_ENV", "testing")

import pytest

from app import create_app
from app.config import TestingConfig
from app.database.connection import db as _db


@pytest.fixture()
def app():
    application = create_app(TestingConfig)

    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db
