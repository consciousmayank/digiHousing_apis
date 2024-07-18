import logging
import pdb

from fastapi import APIRouter, Depends, HTTPException, status
from database.crud import create_record, delete_record, fetch_all_records, update_record

from database.database import Database, Session
from database.database_connection import SessionLocal
from database.database_models import RolesDbModel
from pydantic_models.role_model import Role, RoleUpdate
from pydantic_models.user_model import User, UserUpdate
from security import get_current_user_from_token, is_super_admin, super_admin_required

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(super_admin_required)],
)
async def add_a_new_role(
    role: Role,
    db_session: SessionLocal = Depends(Database().get_db),
    current_user: UserUpdate = Depends(get_current_user_from_token),
):
    logger.info(f"Adding a new role: {role.name}")
    existing_role = (
        db_session.query(RolesDbModel)
        .filter(RolesDbModel.name == role.name)
        .one_or_none()
    )
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role already exists",
        )
    new_role = create_record(
        db=db_session,
        model=RolesDbModel,
        data={"name": role.name},
        current_user_id=current_user.id,
    )
    return {
        "message": f"Role {role.name} added successfully",
    }


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def get_all_the_roles(
    db_session: SessionLocal = Depends(Database().get_db),
):
    logger.info("Fetching all the roles")

    roles = fetch_all_records(db=db_session, model=RolesDbModel)
    return [{"id": role.id, "name": role.name} for role in roles]


@router.put(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(super_admin_required)],
)
async def update_role(
    role: RoleUpdate,
    db_session: SessionLocal = Depends(Database().get_db),
    current_user: UserUpdate = Depends(get_current_user_from_token),
):
    logger.info("Updating role")
    saved_role = (
        db_session.query(RolesDbModel).filter(RolesDbModel.id == role.id).one_or_none()
    )
    if not saved_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    elif saved_role.name == role.name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Role already exists"
        )
    updated_role = update_record(
        db=db_session,
        model=RolesDbModel,
        record_id=saved_role.id,
        data={"name": role.name},
        current_user_id=current_user.id,
    )

    return {"message": "Role updated successfully", "id": updated_role.id}


@router.delete(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(is_super_admin)],
)
async def delete_role(
    role_id: int,
    db_session: SessionLocal = Depends(Database().get_db),
):
    logger.info("Deleting role")
    existing_role = (
        db_session.query(RolesDbModel).filter(RolesDbModel.id == role_id).one_or_none()
    )
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    delete_record(db=db_session, model=RolesDbModel, record_id=role_id)
