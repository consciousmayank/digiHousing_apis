import logging
import pdb
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from database.crud import (
    create_record,
    delete_record,
    fetch_all_records,
    fetch_record,
    update_record,
)
from database.database import Database
from database.database_connection import SessionLocal
from database.database_models import AmenitiesDbModel
from pydantic_models.user_model import User, UserUpdate
from security import get_current_user_from_token, super_admin_or_admin_required

router = APIRouter()

logger = logging.getLogger(__name__)


# Define a model for Amenity
class Amenity(BaseModel):
    """
    Amenity model with name and description
    """

    name: str
    description: str


# Extend Amenity model to include an id for AmenityList
class AmenityList(Amenity):
    """
    AmenityList model with id, name, and description
    """

    id: int


# Function to check if an amenity already exists in the database
def check_if_amenity_already_exists(name: str, db: SessionLocal) -> bool:
    """
    Check if an amenity with the given name already exists in the database.

    Args:
        name (str): The name of the amenity to check.
        db (SessionLocal): The database session.

    Returns:
        bool: True if the amenity already exists, False otherwise.
    """
    logger.info(f"Checking if {name} already exists")
    existing_amenity = (
        db.query(AmenitiesDbModel).filter(AmenitiesDbModel.name == name).one_or_none()
    )
    if existing_amenity:
        raise HTTPException(status_code=400, detail="This amenity already exists")
    return False


# Endpoint to create a new amenity
@router.post(
    "/",
    description="Can only be accessed by super admin or admin",
    name="Create a new amenity",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def create_amenity(
    amenity: Amenity,
    current_user: User = Depends(get_current_user_from_token),
    db_session=Depends(Database().get_db),
):
    """
    Create a new amenity.

    Args:
        amenity (Amenity): The amenity to create.
        current_user (User): The user performing the action.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary with a success message and the ID of the created amenity.
    """
    logger.info(f"Creating amenity {amenity.name} by {current_user.email}")
    if not check_if_amenity_already_exists(amenity.name, db=db_session):
        new_amenity = create_record(
            db=db_session,
            model=AmenitiesDbModel,
            data={
                "name": amenity.name,
                "description": amenity.description,
                "created_by_user": current_user.id,
            },
            current_user_id=current_user.id,
        )
        return {"message": "Amenity added successfully", "id": new_amenity.id}


# Endpoint to update an existing amenity
@router.put(
    "/{amenity_id}",
    description="Can only be accessed by super admin or admin",
    name="Update an amenity",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def update_amenity(
    amenity_id: int,
    amenity: Amenity,
    current_user: User = Depends(get_current_user_from_token),
    db_session=Depends(Database().get_db),
):
    """
    Update an existing amenity.

    Args:
        amenity_id (int): The ID of the amenity to update.
        amenity (Amenity): The updated amenity data.
        current_user (User): The user performing the action.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary with a success message and the ID of the updated amenity.
    """
    existing_amenity = (
        db_session.query(AmenitiesDbModel)
        .filter(AmenitiesDbModel.id == amenity_id)
        .one_or_none()
    )
    if not existing_amenity:
        raise HTTPException(status_code=404, detail="Amenity not found")
    else:
        updated_amenity = update_record(
            db=db_session,
            model=AmenitiesDbModel,
            record_id=amenity_id,
            data={"name": amenity.name, "description": amenity.description},
            current_user_id=current_user.id,
        )
        return {"message": "Amenity updated successfully", "id": updated_amenity.id}


# Endpoint to delete an existing amenity
@router.delete(
    "/{amenity_id}",
    response_model=dict,
    description="Can only be accessed by super admin or admin",
    name="Delete an amenity",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def delete_amenity(
    amenity_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
    current_user: UserUpdate = Depends(get_current_user_from_token),
):
    """
    Delete an existing amenity.

    Args:
        amenity_id (int): The ID of the amenity to delete.
        db_session (SessionLocal): The database session.
        current_user (UserUpdate): The user performing the action.

    Returns:
        dict: A dictionary with a success message.
    """
    existing_amenity = (
        db_session.query(AmenitiesDbModel)
        .filter(AmenitiesDbModel.id == amenity_id)
        .one_or_none()
    )
    if not existing_amenity:
        raise HTTPException(status_code=404, detail="Amenity not found")
    else:
        delete_result = delete_record(
            db=db_session,
            model=AmenitiesDbModel,
            record_id=amenity_id,
            current_user_id=current_user.id,
        )
        return {"message": "Amenity deleted successfully"}


# Endpoint to get all amenities
@router.get(
    "/all",
    response_model=List[AmenityList],
    name="Get all amenities",
    description="Can only be accessed by super admin or admin",
)
async def get_amenities(db_session: SessionLocal = Depends(Database().get_db)):
    """
    Get all amenities.

    Args:
        db_session (SessionLocal): The database session.

    Returns:
        list: A list of all amenities.
    """
    amenities = fetch_all_records(db=db_session, model=AmenitiesDbModel)
    return [amenity.to_dict() for amenity in amenities]


# Endpoint to get an amenity by ID
@router.get(
    "/{amenity_id}",
    response_model=AmenityList,
    name="Get an amenity by ID",
    description="Can only be accessed by super admin or admin",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def get_amenity(
    amenity_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
):
    """
    Get an amenity by ID.

    Args:
        amenity_id (int): The ID of the amenity to get.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary representing the amenity.
    """
    amenity = fetch_record(
        db=db_session, model=AmenitiesDbModel, filter_params={"id": amenity_id}
    )
    return amenity.to_dict()
