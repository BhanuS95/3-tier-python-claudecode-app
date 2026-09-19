"""
Application factory for the Task Management API.

This module wires together configuration, the database layer,
blueprints (routes), logging, and centralized error handling.
No business logic lives here -- see app/services for that.
"""

import logging
import sys

from flask import Flask, jsonify
from flask_cors import CORS

from app.config import get_config
from app.database.connection import db, migrate
from app.health.health_routes import health_bp
from app.routes.task_routes import task_bp


def configure_logging(app: Flask) -> None:
    """
    Configure structured, stdout-based logging.

    Production containers (Docker/Kubernetes) collect stdout/stderr,
    so we never rely on local log files here.
    """
    log_level = app.config.get("LOG_LEVEL", "INFO")

    log_format = "%(asctime)s | %(levelname)-8s | task-management-api | " "%(name)s | %(message)s"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Werkzeug's own logger is noisy at DEBUG; keep it at INFO unless
    # the app itself is in DEBUG mode.
    logging.getLogger("werkzeug").setLevel(logging.DEBUG if log_level == "DEBUG" else logging.INFO)

    app.logger.setLevel(log_level)


def register_error_handlers(app: Flask) -> None:
    """
    Centralized error handling.

    Every error response follows the same JSON envelope:
        { "error": { "code": "...", "message": "..." } }

    Stack traces / internal details are never leaked to the client.
    They are logged server-side instead.
    """

    def _error_response(code: str, message: str, status: int):
        return jsonify({"error": {"code": code, "message": message}}), status

    @app.errorhandler(400)
    def bad_request(err):
        return _error_response("BAD_REQUEST", "The request could not be understood.", 400)

    @app.errorhandler(401)
    def unauthorized(err):
        return _error_response("UNAUTHORIZED", "Authentication is required.", 401)

    @app.errorhandler(403)
    def forbidden(err):
        return _error_response("FORBIDDEN", "You do not have access to this resource.", 403)

    @app.errorhandler(404)
    def not_found(err):
        return _error_response("NOT_FOUND", "The requested resource was not found.", 404)

    @app.errorhandler(405)
    def method_not_allowed(err):
        return _error_response(
            "METHOD_NOT_ALLOWED", "HTTP method not allowed on this endpoint.", 405
        )

    @app.errorhandler(409)
    def conflict(err):
        return _error_response("CONFLICT", "The request conflicts with the current state.", 409)

    @app.errorhandler(422)
    def unprocessable(err):
        return _error_response("VALIDATION_ERROR", "The request payload failed validation.", 422)

    @app.errorhandler(500)
    def internal_error(err):
        app.logger.error("Unhandled exception", exc_info=err)
        return _error_response("INTERNAL_SERVER_ERROR", "An unexpected error occurred.", 500)

    @app.errorhandler(Exception)
    def unhandled_exception(err):
        # Catch-all safety net: never leak stack traces to clients.
        app.logger.error("Unhandled exception", exc_info=err)
        return _error_response("INTERNAL_SERVER_ERROR", "An unexpected error occurred.", 500)


def create_app(config_object=None) -> Flask:
    """
    Application factory. Used by:
      - the dev server (flask run / python run.py)
      - gunicorn in production: gunicorn "app:create_app()"
      - pytest fixtures (with a Testing config override)
    """
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    configure_logging(app)

    # CORS: locked down to the configured origin(s). Defaults to "*"
    # only in local development; production MUST set CORS_ORIGINS.
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(health_bp)
    app.register_blueprint(task_bp, url_prefix="/api/tasks")

    register_error_handlers(app)

    app.logger.info(
        "Application initialized (env=%s, debug=%s)",
        app.config.get("APP_ENV"),
        app.config.get("DEBUG"),
    )

    return app
