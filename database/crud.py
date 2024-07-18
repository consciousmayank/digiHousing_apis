import json
from datetime import datetime
from typing import Any, Dict, Optional, Type

from fastapi import HTTPException
from sqlalchemy.orm import Session

from audit_track.audit_log import add_audit_log


def create_record(db: Session, model: Type[Any], data: Dict[str, Any], current_user_id: int):
    """
    Create a new record in the database and log the action.

    Args:
        db (Session): The database session.
        model (Type[Any]): The SQLAlchemy model class.
        data (Dict[str, Any]): The data to create the new record.
        current_user_id (int): The ID of the user performing the action.

    Returns:
        The newly created record.

    Raises:
        HTTPException: If there's an error during the creation process.
    """
    try:
        new_record = model(**data)
        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        add_audit_log(
            db=db,
            table_name=model.__tablename__,
            record_id=new_record.id,
            changed_by=current_user_id,
            old_values={},
            new_values=data
        )

        return new_record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating record: {str(e)}")

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def update_record(db: Session, model: Type[Any], record_id: int, data: Dict[str, Any], current_user_id: int):
    """
    Update an existing record in the database and log the action.

    Args:
        db (Session): The database session.
        model (Type[Any]): The SQLAlchemy model class.
        record_id (int): The ID of the record to update.
        data (Dict[str, Any]): The new data to update the record with.
        current_user_id (int): The ID of the user performing the action.

    Returns:
        The updated record.

    Raises:
        HTTPException: If the record is not found or if there's an error during the update process.
    """
    try:
        record = db.query(model).filter(model.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")

        old_values = {c.name: getattr(record, c.name) for c in record.__table__.columns}
        old_values_serializable = json.loads(json.dumps(old_values, default=json_serial))

        for key, value in data.items():
            setattr(record, key, value)

        db.commit()
        db.refresh(record)

        new_values_serializable = json.loads(json.dumps(data, default=json_serial))

        add_audit_log(
            db=db,
            table_name=model.__tablename__,
            record_id=record_id,
            changed_by=current_user_id,
            old_values=old_values_serializable,
            new_values=new_values_serializable
        )

        return record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating record: {str(e)}")

def delete_record(db: Session, model: Type[Any], record_id: int, current_user_id: int):
    """
    Delete a record from the database and log the action.

    Args:
        db (Session): The database session.
        model (Type[Any]): The SQLAlchemy model class.
        record_id (int): The ID of the record to delete.
        current_user_id (int): The ID of the user performing the action.

    Returns:
        A dictionary with a success message.

    Raises:
        HTTPException: If the record is not found or if there's an error during the deletion process.
    """
    try:
        record = db.query(model).filter(model.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")

        old_values = {c.name: getattr(record, c.name) for c in record.__table__.columns}
        old_values_serializable = json.loads(json.dumps(old_values, default=json_serial))

        db.delete(record)
        db.commit()

        add_audit_log(
            db=db,
            table_name=model.__tablename__,
            record_id=record_id,
            changed_by=current_user_id,
            old_values=old_values_serializable,
            new_values={}
        )

        return {"message": "record deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting record: {str(e)}")
    
def fetch_all_records(db: Session, model: Type[Any]):
    """
    Fetch all records of a given model from the database.

    Args:
        db (Session): The database session.
        model (Type[Any]): The SQLAlchemy model class.

    Returns:
        A list of all records for the given model.
    """
    return db.query(model).all()



def fetch_record(db: Session, model: Type[Any], filter_params: Dict[str, Any]) -> Optional[Any]:
    """
    Fetch a single record from the database based on the provided filter parameters.

    Args:
        db (Session): The database session.
        model (Type[Any]): The SQLAlchemy model class.
        filter_params (Dict[str, Any]): A dictionary of filter parameters.

    Returns:
        The record matching the filter parameters, or None if not found.

    Raises:
        HTTPException: If there's an error during the fetch process or if multiple records are found.
    """
    try:
        query = db.query(model)
        for attr, value in filter_params.items():
            if hasattr(model, attr):
                query = query.filter(getattr(model, attr) == value)
            else:
                raise HTTPException(status_code=400, detail=f"Invalid filter parameter: {attr}")
        
        records = query.all()
        
        if len(records) == 0:
            raise HTTPException(status_code=404, detail=f"Record not found")
        elif len(records) > 1:
            raise HTTPException(status_code=300, detail=f"Multiple records found")
        
        return records[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching record: {str(e)}")
