"""
Custom application-level exceptions.

Routes catch these and translate them into the standard JSON error
envelope, keeping HTTP concerns out of the service layer.
"""


class AppError(Exception):
    """Base class for all handled application errors."""

    status_code = 500
    code = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationAppError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
