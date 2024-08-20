# from typing import List

import pdb
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import RelationshipProperty, joinedload

from audit_track.audit_log import add_audit_log
from database.crud import (create_record, delete_record, fetch_all_records,
                           fetch_record, update_record)
from database.database import Database
from database.database_connection import SessionLocal
from database.database_models import (AmenitiesDbModel, PropertyAddressDbModel,
                                      QueriesDbModel, QueryTypeEnum)
from pydantic_models.query_model import (QueryList, QueryModel,
                                         QueryStatusUpdate)
from pydantic_models.user_model import User
from security import (get_current_user_from_token,
                      super_admin_or_admin_required, super_admin_required)

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
    """
    Creates a new query in the database.

    Args:
        query (QueryModel): The query data to be created.
        db_session (SessionLocal): The database session.
        current_user (User): The user performing the action.

    Raises:
        HTTPException: If the query type is not 'Buy_a_home' and property_address_id is not provided.
        HTTPException: If an error occurs while creating the record.

    Returns:
        dict: A dictionary with a success message and the ID of the created query.
    """

    try:
        if query.query_type != QueryTypeEnum.Buy_a_home.value and not query.address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="address is required",
            )
        else:
            address = query.address
            if address:
                new_address = PropertyAddressDbModel(
                    house_no=address["house_no"],
                    building_name=address["building_name"],
                    street=address["street"],
                    city=address["city"],
                    state=address["state"],
                    country=address["country"],
                    zip_code=address["zip_code"],
                    created_by_user=current_user.id,
                )
                db_session.add(new_address)
                db_session.flush()
                query.property_address_id = new_address.id

        # Separate relationship data from regular fields
        relationship_data = {}
        model_data = {}
        for key, value in query.model_dump().items():
            if hasattr(QueriesDbModel, key) and isinstance(
                getattr(QueriesDbModel, key).property, RelationshipProperty
            ):
                relationship_data[key] = value
            else:
                model_data[key] = value
        if "address" in model_data:
            del model_data["address"]
        new_record = QueriesDbModel(**model_data)
        db_session.add(new_record)
        db_session.flush()

        # Handle relationships
        for key, value in relationship_data.items():
            if isinstance(value, list):
                related_objects = (
                    db_session.query(
                        getattr(QueriesDbModel, key).property.mapper.class_
                    )
                    .filter(
                        getattr(QueriesDbModel, key).property.mapper.class_.id.in_(
                            value
                        )
                    )
                    .all()
                )
                setattr(new_record, key, related_objects)
            elif value is not None:
                setattr(new_record, key, value)

        db_session.commit()
        db_session.refresh(new_record)

        # Prepare audit log data
        audit_data = model_data.copy()
        for key, value in relationship_data.items():
            if isinstance(value, list):
                audit_data[key] = [item.id for item in getattr(new_record, key)]
            else:
                audit_data[key] = value.id if value else None

        add_audit_log(
            db=db_session,
            table_name=QueriesDbModel.__tablename__,
            record_id=new_record.id,
            changed_by=current_user.id,
            old_values={},
            new_values=audit_data,
        )

        return {"message": "Query added successfully", "query_id": new_record.id}
    except Exception as e:
        db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating record: {str(e)}")


@router.put(
    "/{query_id}",
    response_model=QueryList,
    description="Can only be accessed by super admin or admin",
    name="Update a query",
    # dependencies=[Depends(super_admin_or_admin_required)],
)
async def update_query(
    query_id: int,
    query: QueryModel,
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
):
    existing_query = fetch_record(
        db=db_session, model=QueriesDbModel, filter_params={"id": query_id}
    )
    if not existing_query:
        raise HTTPException(status_code=404, detail="Query not found")

    try:
        # Prepare the update data
        update_data = {
            "user_phonenumber": query.user_phonenumber,
            "user_name": query.user_name,
            "query_type": query.query_type.value,
            "property_type_id": query.property_type_id,
            "property_config_id": query.property_config_id,
            "property_address_id": query.property_address_id,
            "contacted": query.contacted,
            "resolution": query.resolution,
        }

        # If amenities are provided, fetch them
        # if query.amenities is not None:
        #     amenities = (
        #         db_session.query(AmenitiesDbModel)
        #         .filter(AmenitiesDbModel.id.in_(query.amenities))
        #         .all()
        #     )
        #     update_data["amenities"] = amenities

        # Update the query with all data, including amenities if present
        updated_query = update_record(
            db=db_session,
            model=QueriesDbModel,
            record_id=query_id,
            data=update_data,
            current_user_id=current_user.id,
        )

        return updated_query
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating query: {str(e)}")


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
    delete_result = delete_record(
        db=db_session,
        model=QueriesDbModel,
        record_id=query_id,
        current_user_id=current_user.id,
    )
    return delete_result


@router.get(
    "/",
    # response_model=List[QueryList],
    name="Get all queries",
    description="Can only be accessed by super admin or admin",
    # dependencies=[Depends(super_admin_or_admin_required)],
)
async def get_queries(
    db_session: SessionLocal = Depends(Database().get_db),
    page: int = 1,
    page_size: int = 5
):
    # Calculate the offset
    offset = (page - 1) * page_size

    # Query with pagination, and join amenities
    queries = (
        db_session.query(QueriesDbModel)
        .options(joinedload(QueriesDbModel.amenities))
        .order_by(QueriesDbModel.created_at.asc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # Get total count of queries
    total_count = db_session.query(QueriesDbModel).count()

    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size

    return {
        "queries": [query.to_dict() for query in queries],
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages
    }


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
    return fetch_record(
        db=db_session,
        model=QueriesDbModel,
        filter_params={"id": query_id},
        options=[joinedload(QueriesDbModel.amenities)],
    )


@router.put(
    "/{query_id}/contacted",
    response_model=dict,
    name="Update the contacted status of a query",
    description="Can only be accessed by any logged in user",
)
async def update_query_status_post_contacting_user(
    query_id: int,
    query_status_update: QueryStatusUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
):
    return update_record(
        db=db_session,
        model=QueriesDbModel,
        record_id=query_id,
        data={
            "contacted": query_status_update.contacted,
            "resolution": query_status_update.resolution,
        },
        current_user_id=current_user.id,
    )


# Delete all the queries
@router.delete(
    "/",
    response_model=dict,
    name="Delete all queries",
    description="Can only be accessed by super admin",
    dependencies=[Depends(super_admin_required)],
)
async def delete_all_queries(
    db_session: SessionLocal = Depends(Database().get_db),
):
    db_session.query(QueriesDbModel).delete(synchronize_session=False)
    db_session.commit()
    return {"message": "All queries have been deleted successfully."}
