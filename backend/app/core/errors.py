"""Custom exceptions and uniform error handling for VrikshaVision."""

from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from app.config import settings


class AppException(Exception):
    """Base exception class for application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class EntityNotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            code="NOT_FOUND",
            status_code=404,
        )


class InsufficientDataError(AppException):
    """Raised when an operation lacks sufficient data (e.g. < 10 plots for calibration)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INSUFFICIENT_DATA",
            status_code=422,
            details=details,
        )


class ProcessingError(AppException):
    """Raised when pipeline computation encounters a failure."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="PROCESSING_ERROR",
            status_code=500,
            details=details,
        )


class SecurityError(AppException):
    """Raised when authentication or API key validation fails."""

    def __init__(self, message: str = "Invalid or missing API key."):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Formats AppException into consistent API response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "data_source": "synthetic" if settings.MODEL_BACKEND == "mock" else "real",
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled exceptions and returns a clean 500 response."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "UNHANDLED_EXCEPTION",
                "message": str(exc),
            },
            "data_source": "synthetic" if settings.MODEL_BACKEND == "mock" else "real",
        },
    )
