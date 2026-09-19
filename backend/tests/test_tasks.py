"""
Unit + API tests for the Task resource.

Covers: CRUD endpoints, validation errors, not-found scenarios, and
the service layer directly.
"""

import pytest

from app.services import task_service
from app.utils.exceptions import NotFoundError

# ---------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------


def test_create_task_success(client):
    resp = client.post("/api/tasks", json={"title": "Write docs"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["title"] == "Write docs"
    assert body["status"] == "pending"
    assert body["completed"] is False
    assert "id" in body


def test_create_task_missing_title_returns_422(client):
    resp = client.post("/api/tasks", json={})
    assert resp.status_code == 422
    body = resp.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_get_all_tasks(client):
    client.post("/api/tasks", json={"title": "Task 1"})
    client.post("/api/tasks", json={"title": "Task 2"})

    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body) == 2


def test_get_single_task(client):
    created = client.post("/api/tasks", json={"title": "Task"}).get_json()

    resp = client.get(f"/api/tasks/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == created["id"]


def test_get_task_not_found_returns_404(client):
    resp = client.get("/api/tasks/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "TASK_NOT_FOUND"


def test_update_task(client):
    created = client.post("/api/tasks", json={"title": "Old title"}).get_json()

    resp = client.put(
        f"/api/tasks/{created['id']}",
        json={"title": "New title", "status": "in_progress"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["title"] == "New title"
    assert body["status"] == "in_progress"


def test_update_task_not_found_returns_404(client):
    resp = client.put("/api/tasks/does-not-exist", json={"title": "x"})
    assert resp.status_code == 404


def test_update_task_invalid_status_returns_422(client):
    created = client.post("/api/tasks", json={"title": "Task"}).get_json()
    resp = client.put(f"/api/tasks/{created['id']}", json={"status": "not-a-status"})
    assert resp.status_code == 422


def test_delete_task(client):
    created = client.post("/api/tasks", json={"title": "Task"}).get_json()

    resp = client.delete(f"/api/tasks/{created['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/api/tasks/{created['id']}")
    assert resp.status_code == 404


def test_delete_task_not_found_returns_404(client):
    resp = client.delete("/api/tasks/does-not-exist")
    assert resp.status_code == 404


def test_complete_task(client):
    created = client.post("/api/tasks", json={"title": "Task"}).get_json()

    resp = client.patch(f"/api/tasks/{created['id']}/complete")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "completed"
    assert body["completed"] is True


def test_filter_tasks_by_status(client):
    client.post("/api/tasks", json={"title": "A", "status": "pending"})
    b = client.post("/api/tasks", json={"title": "B", "status": "pending"}).get_json()
    client.patch(f"/api/tasks/{b['id']}/complete")

    resp = client.get("/api/tasks?status=completed")
    body = resp.get_json()
    assert len(body) == 1
    assert body[0]["id"] == b["id"]


# ---------------------------------------------------------------------
# Health endpoint tests
# ---------------------------------------------------------------------


def test_liveness_endpoint(client):
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "UP"}


def test_readiness_endpoint(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "UP"
    assert body["database"] == "UP"


# ---------------------------------------------------------------------
# Service-layer (business logic) unit tests
# ---------------------------------------------------------------------


def test_service_create_and_get_task(app):
    with app.app_context():
        task = task_service.create_task({"title": "Service task"})
        fetched = task_service.get_task(task.id)
        assert fetched.title == "Service task"


def test_service_get_missing_task_raises(app):
    with app.app_context(), pytest.raises(NotFoundError):
        task_service.get_task("missing-id")


def test_service_complete_task(app):
    with app.app_context():
        task = task_service.create_task({"title": "Service task"})
        completed = task_service.complete_task(task.id)
        assert completed.status == "completed"
