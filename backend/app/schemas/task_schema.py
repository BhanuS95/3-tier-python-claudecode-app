"""
Request/response validation for Task payloads using Marshmallow.

Schemas are the only place request bodies are trusted from -- routes
never read raw JSON directly into the database layer.
"""

from marshmallow import Schema, fields, validate

from app.models.task import TaskStatus


class TaskCreateSchema(Schema):
    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
    )
    description = fields.String(required=False, allow_none=True, load_default=None)
    status = fields.String(
        required=False,
        load_default=TaskStatus.PENDING,
        validate=validate.OneOf(TaskStatus.ALL),
    )


class TaskUpdateSchema(Schema):
    title = fields.String(required=False, validate=validate.Length(min=1, max=255))
    description = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, validate=validate.OneOf(TaskStatus.ALL))


class TaskResponseSchema(Schema):
    id = fields.String()
    title = fields.String()
    description = fields.String(allow_none=True)
    status = fields.String()
    completed = fields.Method("get_completed")
    created_at = fields.String()
    updated_at = fields.String()

    @staticmethod
    def get_completed(obj) -> bool:
        return obj.status == TaskStatus.COMPLETED


task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_response_schema = TaskResponseSchema()
tasks_response_schema = TaskResponseSchema(many=True)
