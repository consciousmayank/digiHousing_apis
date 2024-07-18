from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import SQLAlchemyError

from config import config
from database.database import Database, Session
from database.database_models import RolesDbModel
from error_handlers import (generic_exception_handler, http_exception_handler,
                            sqlalchemy_exception_handler,
                            validation_exception_handler)
from logging_conf import configure_logging
from routes.amenities import router as amenities_router
from routes.audit import router as audit_router
from routes.property_address import router as property_address_router
from routes.property_configs import router as property_configs_router
from routes.property_type import router as property_type_router
from routes.query_router import router as query_router
from routes.roles_router import router as roles_router
from routes.root import router as root_router
from routes.users import router as users_router

logger = configure_logging()
version = "0.001"

app = FastAPI()


def get_version_based_on_current_date():
    # Get the current time
    now = datetime.now()

    # Format the time
    formatted_time = now.strftime("%d-%B-%Y-%H:%M")

    return formatted_time


app = FastAPI(
    # lifespan=lifespan,
    version=get_version_based_on_current_date(),
    summary="DigiHousing API",
    description="This is the API for DigiHousing",
    contact={"Name": "Mayank", "Phone": "9611886339"},
    title=f"DigiHousing API (Version {get_version_based_on_current_date()})",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    # allow_origins=["http://localhost:64785"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request URL: {request.url}, Method: {request.method}")

    # Read and log the request body
    request_body = await request.body()
    if request_body:
        logger.info(f"Request body: {request_body.decode()}")

    # Call the next middleware and get the response
    response = await call_next(request)

    # Create a custom response to capture the response body for logging
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    logger.info(f"Response body: {response_body.decode()}")

    # Create a new response with the captured body to send it back to the client
    new_response = Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
    return new_response


app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)





app.include_router(root_router)

app.include_router(
    roles_router,
    prefix="/roles",
    tags=["Roles"],
)
app.include_router(
    property_configs_router,
    prefix="/property-configs",
    tags=["Property Configs"],
)
app.include_router(
    property_type_router,
    prefix="/property-type",
    tags=["Property Type"],
)
app.include_router(
    users_router,
    prefix="/user",
    tags=["User"],
)
app.include_router(
    property_address_router,
    prefix="/property-address",
    tags=["Property Address"],
)
app.include_router(
    amenities_router,
    prefix="/amenities",
    tags=["Amenities"],
)
app.include_router(
    query_router,
    prefix="/query",
    tags=["Query"],
)
app.include_router(
    audit_router,
    prefix="/audit",
    tags=["Audit"],
)
