"""
HTTP routes (controllers) for the Task resource.

Flow: HTTP Request -> Route -> Schema validation -> Service layer -> ORM -> PostgreSQL
Routes contain NO business logic and NO direct database queries.
"""

import logging

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.schemas.task_schema import (
    task_create_schema,
    task_response_schema,
    task_update_schema,
    tasks_response_schema,
)
from app.services import task_service
from app.utils.exceptions import AppError

logger = logging.getLogger(__name__)

task_bp = Blueprint("tasks", __name__)


def _error(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status


@task_bp.errorhandler(AppError)
def handle_app_error(err: AppError):
    return _error(err.code, err.message, err.status_code)


@task_bp.errorhandler(ValidationError)
def handle_validation_error(err: ValidationError):
    return _error(
        "VALIDATION_ERROR",
        "; ".join(f"{field}: {', '.join(msgs)}" for field, msgs in err.messages.items())
        or "Invalid request payload.",
        422,
    )


@task_bp.get("")
def get_tasks():
    """GET /api/tasks[?status=pending] -> list all tasks."""
    status = request.args.get("status")
    tasks = task_service.list_tasks(status=status)
    return jsonify(tasks_response_schema.dump(tasks)), 200


@task_bp.get("/<string:task_id>")
def get_task(task_id: str):
    """GET /api/tasks/{id} -> fetch a single task."""
    task = task_service.get_task(task_id)
    return jsonify(task_response_schema.dump(task)), 200


@task_bp.post("")
def create_task():
    """POST /api/tasks -> create a task."""
    payload = task_create_schema.load(request.get_json(silent=True) or {})
    task = task_service.create_task(payload)
    return jsonify(task_response_schema.dump(task)), 201


@task_bp.put("/<string:task_id>")
def update_task(task_id: str):
    """PUT /api/tasks/{id} -> update a task."""
    payload = task_update_schema.load(request.get_json(silent=True) or {})
    task = task_service.update_task(task_id, payload)
    return jsonify(task_response_schema.dump(task)), 200


@task_bp.delete("/<string:task_id>")
def delete_task(task_id: str):
    """DELETE /api/tasks/{id} -> delete a task."""
    task_service.delete_task(task_id)
    return "", 204


@task_bp.patch("/<string:task_id>/complete")
def complete_task(task_id: str):
    """PATCH /api/tasks/{id}/complete -> mark a task completed."""
    task = task_service.complete_task(task_id)
    return jsonify(task_response_schema.dump(task)), 200
