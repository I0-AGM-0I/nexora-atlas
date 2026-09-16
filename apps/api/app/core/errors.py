"""
NEXORA ATLAS - Error Handling & Sanitization
Sanitizes exceptions to prevent leaking internal stack traces or database internals.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import logger


class AtlasException(Exception):
    """Base domain exception for NEXORA ATLAS."""
    def __init__(self, message: str, code: str = "ATLAS_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ProviderError(AtlasException):
    """Cloud provider interaction failure (AWS API errors)."""
    def __init__(self, message: str, provider: str = "AWS", status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(message=message, code=f"{provider}_PROVIDER_ERROR", status_code=status_code)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AtlasException)
    async def atlas_exception_handler(request: Request, exc: AtlasException):
        logger.error(f"Domain exception on {request.method} {request.url.path}: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The submitted payload is invalid.",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact your system administrator.",
                }
            },
        )
