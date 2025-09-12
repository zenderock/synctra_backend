from typing import Optional, Dict, Any

class SynctraException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "SYNCTRA_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(SynctraException):
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )

class AuthenticationException(SynctraException):
    def __init__(self, message: str = "Non authentifié"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationException(SynctraException):
    def __init__(self, message: str = "Non autorisé"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )

class NotFoundException(SynctraException):
    def __init__(self, message: str = "Ressource non trouvée"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND"
        )

class ConflictException(SynctraException):
    def __init__(self, message: str = "Conflit de ressource"):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT_ERROR"
        )

class RateLimitException(SynctraException):
    def __init__(self, message: str = "Limite de taux dépassée"):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED"
        )
