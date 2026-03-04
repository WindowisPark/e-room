import logging
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    AppException,
    NotFoundException,
    ConflictException,
    ForbiddenException,
    UnauthorizedException,
    BadRequestException,
    DatabaseException,
    ErrorMessage,
)

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    NotFoundException:     404,
    ConflictException:     409,
    ForbiddenException:    403,
    UnauthorizedException: 401,
    BadRequestException:   400,
    DatabaseException:     500,
}


async def app_exception_handler(request, exc: AppException) -> JSONResponse:
    status_code = _STATUS_MAP.get(type(exc), 500)
    if status_code >= 500:
        logger.error(f"[AppException] {type(exc).__name__}: {exc.message}")
        message = ErrorMessage.SERVER_ERROR
    else:
        logger.info(f"[AppException] {type(exc).__name__} ({status_code}): {exc.message}")
        message = exc.message
    return JSONResponse(status_code=status_code, content={"detail": message})


async def unhandled_exception_handler(request, exc: Exception) -> JSONResponse:
    logger.error(f"[UnhandledException] {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": ErrorMessage.SERVER_ERROR})
