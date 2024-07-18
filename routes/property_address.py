import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database.crud import (
    create_record,
    delete_record,
    fetch_all_records,
    fetch_record,
    update_record,
)
from database.database import Database
from database.database_connection import SessionLocal
from database.database_models import PropertyAddressDbModel
from pydantic_models.user_model import User
from security import get_current_user_from_token, super_admin_or_admin_required

router = APIRouter()

logger = logging.getLogger(__name__)


# Define a model for PropertyAddress
class PropertyAddress(BaseModel):
    """
    PropertyAddress model with house_no, building_name, street, city, state, country, and zip_code
    """

    house_no: str = Field(..., description="House number")
    building_name: str = Field(..., description="Building name")
    street: str = Field(..., description="Street")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    country: str = Field(..., description="Country")
    zip_code: str = Field(..., description="Zip code")


# Extend PropertyAddress model to include an id for PropertyAddressList
class PropertyAddressList(PropertyAddress):
    """
    PropertyAddressList model with id, house_no, building_name, street, city, state, country, and zip_code
    """

    id: int = Field(..., description="Property address ID")


# Function to check if a property address already exists in the database
def check_if_property_address_already_exists(house_no: str, db: SessionLocal) -> bool:
    """
    Check if a property address with the given house_no already exists in the database.

    Args:
        house_no (str): The house number of the property address to check.
        db (SessionLocal): The database session.

    Returns:
        bool: True if the property address already exists, False otherwise.
    """
    logger.info(f"Checking if {house_no} already exists")
    existing_property_address = (
        db.query(PropertyAddressDbModel)
        .filter(PropertyAddressDbModel.house_no == house_no)
        .one_or_none()
    )
    if existing_property_address:
        raise HTTPException(
            status_code=400, detail="This property address already exists"
        )
    return False


# Endpoint to create a new property address
@router.post(
    "/",
    description="Can only be accessed by super admin or admin",
    name="Create a new property address",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def create_property_address(
    property_address: PropertyAddress,
    current_user: User = Depends(get_current_user_from_token),
    db_session=Depends(Database().get_db),
):
    """
    Create a new property address.

    Args:
        property_address (PropertyAddress): The property address to create.
        current_user (User): The user performing the action.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary with a success message and the ID of the created property address.
    """
    logger.info(
        f"Creating property address {property_address.house_no} by {current_user.email}"
    )
    if not check_if_property_address_already_exists(
        property_address.house_no, db=db_session
    ):
        new_property_address = create_record(
            db=db_session,
            model=PropertyAddressDbModel,
            data={
                "house_no": property_address.house_no,
                "building_name": property_address.building_name,
                "street": property_address.street,
                "city": property_address.city,
                "state": property_address.state,
                "country": property_address.country,
                "zip_code": property_address.zip_code,
                "created_by_user": current_user.id,
            },
            current_user_id=current_user.id,
        )
        return {"message": "Address added successfully", "id": new_property_address.id}


# Endpoint to update an existing property address
@router.put(
    "/{property_address_id}",
    description="Can only be accessed by super admin or admin",
    name="Update a property address",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def update_property_address(
    property_address_id: int,
    property_address: PropertyAddress,
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
):
    """
    Update an existing property address.

    Args:
        property_address_id (int): The ID of the property address to update.
        property_address (PropertyAddress): The updated property address.
        current_user (User): The user performing the action.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary with a success message and the ID of the updated property address.
    """
    existing_property_address = (
        db_session.query(PropertyAddressDbModel)
        .filter(PropertyAddressDbModel.id == property_address_id)
        .one_or_none()
    )
    if not existing_property_address:
        raise HTTPException(status_code=404, detail="Property address not found")
    else:
        updated_property_address = update_record(
            db=db_session,
            model=PropertyAddressDbModel,
            record_id=property_address_id,
            data={
                "house_no": property_address.house_no,
                "building_name": property_address.building_name,
                "street": property_address.street,
                "city": property_address.city,
                "state": property_address.state,
                "country": property_address.country,
                "zip_code": property_address.zip_code,
            },
            current_user_id=current_user.id,
        )
        return {
            "message": "Property address updated successfully",
            "id": updated_property_address.id,
        }


# Endpoint to delete an existing property address
@router.delete(
    "/{property_address_id}",
    response_model=dict,
    description="Can only be accessed by super admin or admin",
    name="Delete a property address",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def delete_property_address(
    property_address_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
    current_user: User = Depends(get_current_user_from_token),
):
    """
    Delete an existing property address.

    Args:
        property_address_id (int): The ID of the property address to delete.
        db_session (SessionLocal): The database session.
        current_user (User): The user performing the action.

    Returns:
        dict: A dictionary with a success message.
    """
    existing_property_address = (
        db_session.query(PropertyAddressDbModel)
        .filter(PropertyAddressDbModel.id == property_address_id)
        .one_or_none()
    )
    if not existing_property_address:
        raise HTTPException(status_code=404, detail="Property address not found")
    else:
        delete_result = delete_record(
            db=db_session,
            model=PropertyAddressDbModel,
            record_id=property_address_id,
            current_user_id=current_user.id,
        )
        return {"message": "Address deleted successfully"}


# Endpoint to get all property addresses
@router.get(
    "/",
    response_model=List[PropertyAddressList],
    name="Get all property addresses",
    description="Can only be accessed by super admin or admin",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def get_property_addresses(
    db_session: SessionLocal = Depends(Database().get_db),
):
    """
    Get all property addresses.

    Args:
        db_session (SessionLocal): The database session.

    Returns:
        list: A list of all property addresses.
    """
    addresses = fetch_all_records(db=db_session, model=PropertyAddressDbModel)
    return [address.to_dict() for address in addresses]


# Endpoint to get a property address by ID
@router.get(
    "/{property_address_id}",
    response_model=PropertyAddressList,
    name="Get a property address by ID",
    description="Can only be accessed by super admin or admin",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def get_property_address(
    property_address_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
):
    """
    Get a property address by ID.

    Args:
        property_address_id (int): The ID of the property address to get.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary representing the property address.
    """
    address = fetch_record(
        db=db_session,
        model=PropertyAddressDbModel,
        filter_params={"id": property_address_id},
    )
    return address.to_dict()
