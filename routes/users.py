import logging

from fastapi import APIRouter, Depends, HTTPException, status

from database.database import Database, Session
from database.database_connection import SessionLocal
from database.database_models import RolesDbModel, UserDbModel
from pydantic_models.user_model import UserIn, UserInWithRole
from security import (authenticate_user, create_access_token,
                      get_password_hash, get_user, super_admin_required)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/register/role", status_code=status.HTTP_201_CREATED)
async def register_user_with_a_role(user: UserInWithRole, db_session: SessionLocal = Depends(Database().get_db),):
    role_corresponding_to_role_id = db_session.query(
        RolesDbModel
    ).filter(
        RolesDbModel.id == user.role_id
    ).one_or_none()
    if role_corresponding_to_role_id is None:
        all_the_allowed_roles = db_session.query(RolesDbModel).all()
        message = {
            "message": "Role Not Found",
            "roles" : [single_role.name for single_role in all_the_allowed_roles]
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    role_id = role_corresponding_to_role_id.id
    if role_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found"
        )
    return await register_user(user=user, role_id=role_id, db_session=db_session)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_a_user(user: UserIn, db_session: SessionLocal = Depends(Database().get_db),):
    
    end_user_id = (
        db_session.query(RolesDbModel).filter(
            RolesDbModel.name == "endUser"
        ).one()
    ).id

    return await register_user(user=user, role_id=end_user_id, db_session=db_session)




@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(super_admin_required)],
)
async def get_all_end_users_list(db_session: SessionLocal = Depends(Database().get_db),):
    all_users = db_session.query(UserDbModel).all()
    return [
        {
            "id": singleUser.id,
            "email": singleUser.email_id,
            "role": singleUser.role.name,
        }
        for singleUser in all_users
    ]


@router.post("/token", status_code=status.HTTP_200_OK)
async def login(user: UserIn, db_session: SessionLocal = Depends(Database().get_db)):
    user = await authenticate_user(email=user.email, password=user.password, db=db_session)
    access_token = create_access_token(email=user.email_id)
    return {"access_token": access_token, "token_type": "bearer"}


async def register_user(user: UserIn, role_id: int, db_session: SessionLocal):
    if await get_user(email=user.email, db=db_session):
        logger.error(
            "User with this email already exists",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    logger.info(
        "Fetching user",
    )
    new_user = UserDbModel(
        email_id=user.email,
        password=get_password_hash(
            password=user.password,
        ),
        role_id=role_id,
    )
    db_session.add(new_user)
    db_session.commit()
    logger.info(
        "User created",
    )
    return {"detail": "User created"}
