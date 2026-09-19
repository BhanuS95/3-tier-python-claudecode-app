"""
Business logic for Task management.

This layer knows nothing about HTTP or Flask -- it accepts and
returns plain Python objects / dicts and raises AppError subclasses
on failure. Routes are responsible for turning these into HTTP
responses.
"""

import logging

from app.database.connection import db
from app.models.task import Task, TaskStatus
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


def list_tasks(status: str | None = None) -> list[Task]:
    query = Task.query
    if status:
        query = query.filter(Task.status == status)
    return query.order_by(Task.created_at.desc()).all()


def get_task(task_id: str) -> Task:
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError(f"Task '{task_id}' was not found.", code="TASK_NOT_FOUND")
    return task


def create_task(data: dict) -> Task:
    task = Task(
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", TaskStatus.PENDING),
    )
    db.session.add(task)
    db.session.commit()
    logger.info("Task created id=%s", task.id)
    return task


def update_task(task_id: str, data: dict) -> Task:
    task = get_task(task_id)

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        task.status = data["status"]

    db.session.commit()
    logger.info("Task updated id=%s", task.id)
    return task


def delete_task(task_id: str) -> None:
    task = get_task(task_id)
    db.session.delete(task)
    db.session.commit()
    logger.info("Task deleted id=%s", task_id)


def complete_task(task_id: str) -> Task:
    task = get_task(task_id)
    task.status = TaskStatus.COMPLETED
    db.session.commit()
    logger.info("Task marked complete id=%s", task.id)
    return task
