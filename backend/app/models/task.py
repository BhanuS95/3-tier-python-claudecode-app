"""
SQLAlchemy ORM model for the `tasks` table.
"""

import uuid
from datetime import datetime, timezone

from app.database.connection import db


class TaskStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    ALL = (PENDING, IN_PROGRESS, COMPLETED)


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=TaskStatus.PENDING,
        server_default=TaskStatus.PENDING,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.CheckConstraint(f"status IN {tuple(TaskStatus.ALL)}", name="ck_tasks_status_valid"),
        db.Index("ix_tasks_status", "status"),
        db.Index("ix_tasks_created_at", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "completed": self.status == TaskStatus.COMPLETED,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"
