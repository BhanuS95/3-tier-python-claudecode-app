"""
Health check endpoints for orchestration platforms (Docker, Kubernetes).

- /health/live  : Liveness  - is the process running / not deadlocked?
                  Must NOT check external dependencies. If this fails,
                  Kubernetes will restart the pod.
- /health/ready : Readiness - can the app currently serve traffic?
                  Checks dependencies (PostgreSQL). If this fails,
                  Kubernetes removes the pod from the Service's
                  load-balancing rotation WITHOUT restarting it.
"""

from flask import Blueprint, jsonify

from app.database.connection import check_database_connection

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.get("/live")
def liveness():
    return jsonify({"status": "UP"}), 200


@health_bp.get("/ready")
def readiness():
    database_up = check_database_connection()
    payload = {
        "status": "UP" if database_up else "DOWN",
        "database": "UP" if database_up else "DOWN",
    }
    status_code = 200 if database_up else 503
    return jsonify(payload), status_code
