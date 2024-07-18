import logging
import pdb
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.crud import create_record, delete_record, fetch_all_records, update_record

from database.database import Database
from database.database_connection import SessionLocal
from database.database_models import PropertyConfigDbModel
from pydantic_models.property import (PropertyConfig, PropertyConfigList,
                                      PropertyType, PropertyTypeList,
                                      PropertyTypeUpdate)
from pydantic_models.user_model import User, UserUpdate
from security import get_current_user_from_token, super_admin_or_admin_required

router = APIRouter()


logger = logging.getLogger(__name__)


async def check_if_property_config_already_exists(
    type_name: str, db_session: SessionLocal = Depends(Database().get_db)
):
    if await db_session.execute(
        PropertyConfigDbModel.select().where(
            PropertyConfigDbModel.name == type_name,
        )
    ).one():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This property config already exists",
        )


# PropertyConfig Endpoints
@router.post(
    "/",
    name="Create a new property config",
    description="Can only be accessed by super admin or admin",
    dependencies=[
        Depends(super_admin_or_admin_required),
    ],
)
async def create_property_config(
    property_config: PropertyConfig,
    current_user: Annotated[UserUpdate, Depends(get_current_user_from_token)],
    db_session: SessionLocal = Depends(Database().get_db),
):
    logger.info(f"Adding a new property config: {property_config.name}")
    existing_property_config = db_session.query(PropertyConfigDbModel).filter(
        PropertyConfigDbModel.name == property_config.name
    ).one_or_none()
    if existing_property_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PropertyConfig already exists",
        )
    new_property_config = create_record(
        db=db_session,
        model=PropertyConfigDbModel,
        data={
            "name": property_config.name,
            "description": property_config.description,
            "created_by_user": current_user.id,
        },
        current_user_id=current_user.id,
    )
    return {"message": "Property config added successfully", "id": new_property_config.id}


@router.put(
    "/{property_config_id}",
    name="Update a property config",
    description="Can only be accessed by super admin or admin",
    dependencies=[
        Depends(
            super_admin_or_admin_required,
        ),
    ],
)
async def update_property_config(
    property_config_id: int,
    property_config: PropertyConfig,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db_session: SessionLocal = Depends(Database().get_db),
):
    existing_property_config = (
        db_session.query(PropertyConfigDbModel)
        .filter(PropertyConfigDbModel.id == property_config_id)
        .one_or_none()
    )
    if not existing_property_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property config not found",
        )
    else:
        updated_property_config = update_record(
            db=db_session,
            model=PropertyConfigDbModel,
            record_id=property_config_id,
            data={
                "name": property_config.name,
                "description": property_config.description,
            },
            current_user_id=current_user.id,
        )
        return {
            "message": "Property config updated successfully",
            "id": updated_property_config.id,
        }


@router.delete(
    "/{property_config_id}",
    response_model=dict,
    name="Delete a property config",
    description="Can only be accessed by super admin or admin",
    dependencies=[
        Depends(
            super_admin_or_admin_required,
        ),
    ],
)
async def delete_property_config(
    property_config_id: int,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db_session: SessionLocal = Depends(Database().get_db),
):
    deleted_property_config = (
        db_session.query(PropertyConfigDbModel)
        .filter(PropertyConfigDbModel.id == property_config_id)
        .one_or_none()
    )

    if not deleted_property_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property config not found",
        )
    else:
        delete_result = delete_record(
            db=db_session,
            model=PropertyConfigDbModel,
            record_id=property_config_id,
            current_user_id=current_user.id,
        )
        return {"message": "Property config deleted successfully"}


@router.get(
    "/",
    name="Get all property configs",
    description="Can only be accessed by super admin or admin",
)
async def get_property_configs(
    db_session: SessionLocal = Depends(Database().get_db),
):
    property_configs = fetch_all_records(db=db_session, model=PropertyConfigDbModel)
    return [property_config.to_dict() for property_config in property_configs]
