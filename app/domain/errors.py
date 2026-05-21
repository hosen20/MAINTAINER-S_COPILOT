class DomainError(Exception):
    code = "domain_error"
    status_code = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404


class PermissionDeniedError(DomainError):
    code = "permission_denied"
    status_code = 403


class ValidationError(DomainError):
    code = "validation_error"
    status_code = 422


class ToolFailureError(DomainError):
    code = "tool_failure"
    status_code = 502


class InfrastructureError(DomainError):
    code = "infrastructure_error"
    status_code = 503