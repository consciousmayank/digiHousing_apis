from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.crud import (create_record, delete_record, fetch_all_records,
                           fetch_record, update_record)
from database.database import Database
from database.database_connection import SessionLocal
from database.database_models import PropertyTypesDbModel
from pydantic_models.property import (PropertyConfig, PropertyConfigList,
                                      PropertyType, PropertyTypeList,
                                      PropertyTypeUpdate)
from pydantic_models.user_model import User
from security import get_current_user_from_token, super_admin_or_admin_required

router = APIRouter()


def check_if_property_type_with_name_exists(
    name: str, db_session: SessionLocal
) -> bool:
    property_type = (
        db_session.query(PropertyTypesDbModel)
        .filter(PropertyTypesDbModel.name == name)
        .one_or_none()
    )
    if property_type:
        raise HTTPException(status_code=400, detail="Property type already exists")
    else:
        return False
def check_if_property_type_with_id_exists(
    id: str, db_session: SessionLocal
) -> bool:
    property_type = (
        db_session.query(PropertyTypesDbModel)
        .filter(PropertyTypesDbModel.id == id)
        .one_or_none()
    )
    if not property_type:
        raise HTTPException(status_code=400, detail="Property type not found")
    else:
        return True


# PropertyType Endpoints
@router.post(
    "/",
    description="Can only be accessed by super admin or admin",
    name="Create a new property type ",
    dependencies=[
        Depends(
            super_admin_or_admin_required,
        ),
    ],
)
async def create_property_type(
    property_type: PropertyType,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db_session: SessionLocal = Depends(Database().get_db),
):
    if not check_if_property_type_with_name_exists(property_type.name, db_session=db_session):
        new_property_type = create_record(
            db=db_session,
            model=PropertyTypesDbModel,
            data={
                "name": property_type.name,
                "description": property_type.description,
                "created_by_user": current_user.id,
            },
            current_user_id=current_user.id,
        )
        return {"message": "Property type added successfully", "id": new_property_type.id}


@router.put(
    "/{property_type_id}",
    description="Can only be accessed by super admin or admin",
    name="Update a property type",
    dependencies=[
        Depends(
            super_admin_or_admin_required,
        ),
    ],
)
async def update_property_type(
    property_type_id: int,
    property_type: PropertyType,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db_session: SessionLocal = Depends(Database().get_db),
):
    if not check_if_property_type_with_name_exists(property_type.name, db_session=db_session):
        updated_property_type = update_record(
            db=db_session,
            model=PropertyTypesDbModel,
            record_id=property_type_id,
            data={
                "name": property_type.name,
                "description": property_type.description,
                "created_by_user": current_user.id,
            },
            current_user_id=current_user.id,
        )
        return {"message": "Property type updated successfully", "id": updated_property_type.id}


@router.delete(
    "/{property_type_id}",
    description="Can only be accessed by super admin or admin",
    name="Delete a property type",
    dependencies=[
        Depends(
            super_admin_or_admin_required,
        ),
    ],
)
async def delete_property_type(
    property_type_id: int,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db_session: SessionLocal = Depends(Database().get_db),
):
    if check_if_property_type_with_id_exists(property_type_id, db_session=db_session):
        delete_result = delete_record(
            db=db_session,
            model=PropertyTypesDbModel,
            record_id=property_type_id,
            current_user_id=current_user.id,
        )
        return {"message": "Property type deleted successfully", "id": property_type_id}


@router.get(
    "/",
    description="Can only be accessed by super admin or admin",
    name="Get all property types",
)
async def get_property_types(db_session: SessionLocal = Depends(Database().get_db)):
    property_types = fetch_all_records(db=db_session, model=PropertyTypesDbModel)
    if not property_types:
        raise HTTPException(status_code=404, detail="No property types found")
    return [
        property_type.to_dict()
        for property_type in property_types
    ]


@router.get(
    "/{property_config_id}",
    name="Get a property config by ID",
    description="Can only be accessed by super admin or admin",
    dependencies=[
        Depends(
            super_admin_or_admin_required,
        ),
    ],
)
async def get_property_config(property_config_id: int, db_session: SessionLocal = Depends(Database().get_db)):
    property_type = fetch_record(db=db_session, model=PropertyTypesDbModel, filter_params={"id": property_config_id})
    if not property_type:
        raise HTTPException(status_code=404, detail="Property type not found")
    return property_type.to_dict()