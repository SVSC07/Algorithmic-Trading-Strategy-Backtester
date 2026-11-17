"""
core/errors.py
Maps every domain exception to the JSON error envelope defined in the contract.

Error envelope: {"error": {"code": "...", "message": "..."}}
FastAPI RequestValidationError → 400 VALIDATION_ERROR
Catch-all handler → 500 INTERNAL_ERROR (no internals leaked).
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.domain import (
    AuthError,
    ConflictError,
    ForbiddenError,
    InsufficientDataError,
    NotFoundError,
    ValidationError,
)


def _envelope(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to *app*."""

    @app.exception_handler(ValidationError)
    async def handle_validation(_req: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content=_envelope("VALIDATION_ERROR", str(exc)),
        )

    @app.exception_handler(AuthError)
    async def handle_auth(_req: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_401_UNAUTHORIZED,
            content=_envelope("UNAUTHENTICATED", str(exc)),
        )

    @app.exception_handler(ForbiddenError)
    async def handle_forbidden(_req: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_403_FORBIDDEN,
            content=_envelope("FORBIDDEN", str(exc)),
        )

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_req: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_404_NOT_FOUND,
            content=_envelope("NOT_FOUND", str(exc)),
        )

    @app.exception_handler(ConflictError)
    async def handle_conflict(_req: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_409_CONFLICT,
            content=_envelope("CONFLICT", str(exc)),
        )

    @app.exception_handler(InsufficientDataError)
    async def handle_insufficient(_req: Request, exc: InsufficientDataError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_envelope("INSUFFICIENT_DATA", str(exc)),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        _req: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Remap FastAPI's 422 validation errors to 400 VALIDATION_ERROR."""
        messages = "; ".join(
            f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}"
            for e in exc.errors()
        )
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content=_envelope("VALIDATION_ERROR", messages),
        )

    @app.exception_handler(Exception)
    async def handle_generic(_req: Request, _exc: Exception) -> JSONResponse:
        """Catch-all: 500, no internals leaked."""
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("INTERNAL_ERROR", "An unexpected error occurred"),
        )
