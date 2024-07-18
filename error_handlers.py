import logging
from sqlite3 import IntegrityError

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": exc.detail},
    )
def IntegrityError_handler(request: Request, exc: IntegrityError):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": exc.detail},
    )


def validation_exception_handler(request: Request, exc: RequestValidationError):

    data = exc.errors()

    # Extract error messages
    error_messages = {error["loc"][-1]: error["msg"] for error in data}

    # Print the result
    print(error_messages)

    logger.error(f"Validation error: {error_messages}")
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "message": error_messages},
    )


def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "database_error", "message": str(exc)},
    )


def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    logger.info(f"Unexpected info: {str(exc)}")
    logger.debug(f"Unexpected debug: {str(exc)}")
    logger.warning(f"Unexpected warning: {str(exc)}")
    logger.critical(f"Unexpected critical: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": str(exc)},
    )
