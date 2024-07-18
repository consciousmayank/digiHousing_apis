import pdb
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from database.crud import create_record, delete_record, fetch_all_records, fetch_record, update_record

from database.database import Database
from database.database_connection import SessionLocal
from database.database_models import QueriesDbModel, QueryTypeEnum
from pydantic_models.query_model import (QueryList, QueryModel,
                                         QueryStatusUpdate)
from pydantic_models.user_model import User
from security import get_current_user_from_token, super_admin_or_admin_required

router = APIRouter()


@router.post(
    "/",
    description="Can only be accessed by super admin or admin",
    name="Create a new query",
)
async def create_query(
    query: QueryModel,
    db_session: SessionLocal = Depends(Database().get_db),
    current_user: User = Depends(get_current_user_from_token),
):
    # property_address_id cannot be null unless query_type is "Buy_a_home"
    if (
        query.query_type != QueryTypeEnum.Buy_a_home.value
        and not query.property_address_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="address is required",
        )

    try:
        new_query = create_record(
            db=db_session,
            model=QueriesDbModel,
            data={
                "user_phonenumber": query.user_phonenumber,
                "user_name": query.user_name,
                "query_type": query.query_type.value,
                "property_type_id": query.property_type_id,
                "property_config_id": query.property_config_id,
                "property_address_id": query.property_address_id,
                "amenities_id": query.amenities_id,
            },
            current_user_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding query: {e}")
    return {"message": "Query added successfully"}


@router.put(
    "/{query_id}",
    response_model=QueryList,
    description="Can only be accessed by super admin or admin",
    name="Update a query",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def update_query(
    query_id: int,
    query: QueryModel,
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
):
    existing_query = fetch_record(db=db_session, model=QueriesDbModel, filter_params={"id": query_id})
    if not existing_query:
        raise HTTPException(status_code=404, detail="Query not found")
    else:
        updated_query = update_record(
            db=db_session,
            model=QueriesDbModel,
            record_id=query_id,
            data=query.dict(),
            current_user_id=current_user.id,
        )
        return updated_query


"""
Deletes a query by the given 'query_id'.

Can only be accessed by super admin or admin users.

Args:
    query_id (int): The ID of the query to delete.

Returns:
    dict: A dictionary containing the success message.
"""


@router.delete(
    "/{query_id}",
    response_model=dict,
    description="Can only be accessed by super admin or admin",
    name="Delete a query",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def delete_query(
    query_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
    current_user: User = Depends(get_current_user_from_token),
):
    query_to_delete = db_session.query(QueriesDbModel).filter(QueriesDbModel.id == query_id).one_or_none()
    if not query_to_delete:
        raise HTTPException(status_code=404, detail="Query not found")
    else:
        delete_result = delete_record(
            db=db_session,
            model=QueriesDbModel,
            record_id=query_id,
            current_user_id=current_user.id,
        )
        return delete_result


@router.get(
    "/",
    response_model=List[QueryList],
    name="Get all queries",
    description="Can only be accessed by super admin or admin",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def get_queries(
    db_session: SessionLocal = Depends(Database().get_db),
):
    return fetch_all_records(db=db_session, model=QueriesDbModel)


@router.get(
    "/{query_id}",
    response_model=QueryList,
    name="Get a query by ID",
    description="Can only be accessed by super admin or admin",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def get_query(
    query_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
):
    return fetch_record(db=db_session, model=QueriesDbModel, filter_params={"id": query_id})


@router.put(
    "/{query_id}/contacted",
    response_model=dict,
    name="Update the contacted status of a query",
    description="Can only be accessed by any logged in user",
)
async def update_query_status_post_contacting_user(
    query_id: int,
    query_status_update: QueryStatusUpdate,
    current_user: User = Depends(
        get_current_user_from_token,
    ),
    db_session: SessionLocal = Depends(Database().get_db),
):
    return await update_record(
        db=db_session,
        model=QueriesDbModel,
        record_id=query_id,
        update_data={
            "contacted": query_status_update.contacted,
            "resolution": query_status_update.resolution,
        },
        success_message="Query updated successfully",
        changed_by=current_user.id,
    )
