"""Hierarchie d'exceptions unifiee."""

from __future__ import annotations


class BrainyError(Exception):
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", http_status: int = 500, details: dict | None = None):
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}
        super().__init__(message)


class ValidationError(BrainyError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "VALIDATION_ERROR", 400, **kwargs)


class NotFoundError(BrainyError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, "NOT_FOUND", 404, **kwargs)


class ProviderError(BrainyError):
    def __init__(self, message: str, provider: str, **kwargs):
        super().__init__(message, "PROVIDER_ERROR", 503, details={"provider": provider}, **kwargs)