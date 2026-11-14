# STUB, owned by Molik, replaced on merge
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.domain import (
    ValidationError,
    AuthError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    InsufficientDataError,
)

def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        # Remap FastAPI 422 to 400 so 422 is reserved strictly for INSUFFICIENT_DATA
        messages = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            messages.append(f"{loc}: {err.get('msg')}")
        msg = "; ".join(messages) if messages else "Invalid request data"
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "VALIDATION_ERROR", "message": msg}},
        )

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError):
        return JSONResponse(
            status_code=401,
            content={"error": {"code": "UNAUTHENTICATED", "message": str(exc)}},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_error_handler(request: Request, exc: ForbiddenError):
        return JSONResponse(
            status_code=403,
            content={"error": {"code": "FORBIDDEN", "message": str(exc)}},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": str(exc)}},
        )

    @app.exception_handler(ConflictError)
    async def conflict_error_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "CONFLICT", "message": str(exc)}},
        )

    @app.exception_handler(InsufficientDataError)
    async def insufficient_data_error_handler(request: Request, exc: InsufficientDataError):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "INSUFFICIENT_DATA", "message": str(exc)}},
        )
