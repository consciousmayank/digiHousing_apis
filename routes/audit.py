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
from database.database_models import AuditLogsDbModel
from pydantic_models.user_model import User, UserUpdate
from security import get_current_user_from_token, super_admin_or_admin_required

router = APIRouter()

logger = logging.getLogger(__name__)


# Define a model for Audit Log
class AuditLog(BaseModel):
    """
    AuditLog model with action, table_name, record_id, changed_by, old_values, and new_values
    """

    action: str
    table_name: str
    record_id: int
    changed_by: int
    old_values: dict
    new_values: dict


# Extend AuditLog model to include an id for AuditLogList
class AuditLogList(AuditLog):
    """
    AuditLogList model with id, action, table_name, record_id, changed_by, old_values, and new_values
    """

    id: int


# Function to check if an audit log already exists in the database
def check_if_audit_log_already_exists(record_id: int, db: SessionLocal) -> bool:
    """
    Check if an audit log with the given record_id already exists in the database.

    Args:
        record_id (int): The record_id of the audit log to check.
        db (SessionLocal): The database session.

    Returns:
        bool: True if the audit log already exists, False otherwise.
    """
    logger.info(f"Checking if audit log for record_id {record_id} already exists")
    existing_audit_log = (
        db.query(AuditLogsDbModel).filter(AuditLogsDbModel.record_id == record_id).one_or_none()
    )
    if existing_audit_log:
        raise HTTPException(status_code=400, detail="This audit log already exists")
    return False


# Endpoint to create a new audit log
@router.post(
    "/",
    description="Can only be accessed by super admin or admin",
    name="Create a new audit log",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def create_audit_log(
    audit_log: AuditLog,
    current_user: User = Depends(get_current_user_from_token),
    db_session=Depends(Database().get_db),
):
    """
    Create a new audit log.

    Args:
        audit_log (AuditLog): The audit log to create.
        current_user (User): The user performing the action.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary with a success message and the ID of the created audit log.
    """
    logger.info(f"Creating audit log for {audit_log.record_id} by {current_user.email}")
    if not check_if_audit_log_already_exists(audit_log.record_id, db=db_session):
        new_audit_log = create_record(
            db=db_session,
            model=AuditLogsDbModel,
            data={
                "action": audit_log.action,
                "table_name": audit_log.table_name,
                "record_id": audit_log.record_id,
                "changed_by": current_user.id,
                "old_values": audit_log.old_values,
                "new_values": audit_log.new_values,
            },
            current_user_id=current_user.id,
        )
        return {"message": "Audit log added successfully", "id": new_audit_log.id}


# Endpoint to update an existing audit log
@router.put(
    "/{audit_log_id}",
    description="Can only be accessed by super admin or admin",
    name="Update an audit log",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def update_audit_log(
    audit_log_id: int,
    audit_log: AuditLog,
    current_user: User = Depends(get_current_user_from_token),
    db_session=Depends(Database().get_db),
):
    """
    Update an existing audit log.

    Args:
        audit_log_id (int): The ID of the audit log to update.
        audit_log (AuditLog): The updated audit log data.
        current_user (User): The user performing the action.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary with a success message and the ID of the updated audit log.
    """
    existing_audit_log = (
        db_session.query(AuditLogsDbModel)
        .filter(AuditLogsDbModel.id == audit_log_id)
        .one_or_none()
    )
    if not existing_audit_log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    else:
        updated_audit_log = update_record(
            db=db_session,
            model=AuditLogsDbModel,
            record_id=audit_log_id,
            data={
                "action": audit_log.action,
                "table_name": audit_log.table_name,
                "record_id": audit_log.record_id,
                "changed_by": current_user.id,
                "old_values": audit_log.old_values,
                "new_values": audit_log.new_values,
            },
            current_user_id=current_user.id,
        )
        return {"message": "Audit log updated successfully", "id": updated_audit_log.id}


# Endpoint to delete an existing audit log
@router.delete(
    "/{audit_log_id}",
    response_model=dict,
    description="Can only be accessed by super admin or admin",
    name="Delete an audit log",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def delete_audit_log(
    audit_log_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
    current_user: UserUpdate = Depends(get_current_user_from_token),
):
    """
    Delete an existing audit log.

    Args:
        audit_log_id (int): The ID of the audit log to delete.
        db_session (SessionLocal): The database session.
        current_user (UserUpdate): The user performing the action.

    Returns:
        dict: A dictionary with a success message.
    """
    existing_audit_log = (
        db_session.query(AuditLogsDbModel)
        .filter(AuditLogsDbModel.id == audit_log_id)
        .one_or_none()
    )
    if not existing_audit_log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    else:
        delete_result = delete_record(
            db=db_session,
            model=AuditLogsDbModel,
            record_id=audit_log_id,
            current_user_id=current_user.id,
        )
        return {"message": "Audit log deleted successfully"}


# Endpoint to get all audit logs
@router.get(
    "/all",
    response_model=List[AuditLogList],
    name="Get all audit logs",
    description="Can only be accessed by super admin or admin",
)
async def get_audit_logs(db_session: SessionLocal = Depends(Database().get_db)):
    """
    Get all audit logs.

    Args:
        db_session (SessionLocal): The database session.

    Returns:
        list: A list of all audit logs.
    """
    audit_logs = fetch_all_records(db=db_session, model=AuditLogsDbModel)
    return [audit_log.to_dict() for audit_log in audit_logs]


# Endpoint to get an audit log by ID
@router.get(
    "/{audit_log_id}",
    response_model=AuditLogList,
    name="Get an audit log by ID",
    description="Can only be accessed by super admin or admin",
    dependencies=[Depends(super_admin_or_admin_required)],
)
async def get_audit_log(
    audit_log_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
):
    """
    Get an audit log by ID.

    Args:
        audit_log_id (int): The ID of the audit log to get.
        db_session (SessionLocal): The database session.

    Returns:
        dict: A dictionary representing the audit log.
    """
    audit_log = fetch_record(
        db=db_session, model=AuditLogsDbModel, filter_params={"id": audit_log_id}
    )
    return audit_log.to_dict()
