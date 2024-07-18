import datetime
import logging
import pdb
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from config import config
from database.database import Database, Session, db
from database.database_connection import SessionLocal
from database.database_models import (AuditLogsDbModel, RolesDbModel,
                                      UserDbModel)
from pydantic_models.user_model import User, UserUpdate

logger = logging.getLogger(__name__)
pwd_context = CryptContext(
    schemes=["bcrypt"],
)
oath2_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)  # the endpoint name which creates the token


async def get_role_ids(db_session: SessionLocal):
    admin_role = (
        db_session.query(RolesDbModel)
        .filter(RolesDbModel.name == "admin")
        .one_or_none()
    )
    if admin_role is None:
        raise HTTPException(
            status_code=500, detail="Admin role not found in the database"
        )
    super_admin_role = (
        db_session.query(RolesDbModel)
        .filter(RolesDbModel.name == "superAdmin")
        .one_or_none()
    )
    if super_admin_role is None:
        raise HTTPException(
            status_code=500, detail="Super Admin role not found in the database"
        )
    end_user_role = (
        db_session.query(RolesDbModel)
        .filter(RolesDbModel.name == "endUser")
        .one_or_none()
    )
    if end_user_role is None:
        raise HTTPException(
            status_code=500, detail="End User role not found in the database"
        )
    return admin_role.id, super_admin_role.id, end_user_role.id


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

token_expired_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token has expired",
    headers={"WWW-Authenticate": "Bearer"},
)


def access_token_expiry_minutes() -> int:
    return 30


def create_access_token(email: str):
    logger.info("Creating access token", extra={"email": email})
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=access_token_expiry_minutes(),
    )
    jwt_data = {"sub": email, "exp": expire}
    logger.info("algo :: ", extra={"algo": config.ALGORITHM})
    logger.info("key :: ", extra={"key": config.TOKEN_SECRET_KEY})
    logger.info("encoded_jwt")
    encoded_jwt = jwt.encode(
        jwt_data, key=config.TOKEN_SECRET_KEY, algorithm=config.ALGORITHM
    )
    # encoded_jwt = jwt.encode(jwt_data, 'secret', algorithm='HS256')
    return encoded_jwt


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_text_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_text_password, hashed_password)


async def get_user(email: str, db: SessionLocal) -> dict:
    logger.debug("Fetching user from DB", extra={"email": email})
    query = db.query(UserDbModel).filter(UserDbModel.email_id == email).first()
    logger.debug("Query", extra={"query": query})
    return query


async def authenticate_user(email: str, password: str, db: SessionLocal):
    logger.debug("Authenticating user", extra={"email": email})
    user = await get_user(email, db=db)
    if not user:
        raise credentials_exception
    if not verify_password(password, user.password):
        raise credentials_exception
    return user


async def get_current_user_from_token(
    token: Annotated[str, Depends(oath2_scheme)],
    db: Session = Depends(Database().get_db),
) -> UserUpdate:
    try:
        payload = jwt.decode(
            token, key=config.TOKEN_SECRET_KEY, algorithms=[config.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except ExpiredSignatureError as error:
        raise token_expired_exception from error
    except JWTError as error:
        raise credentials_exception from error
    user = await get_user(email=email, db=db)
    if user is None:
        raise credentials_exception
    return UserUpdate(email=user.email_id, id=user.id)


async def super_admin_required(
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
):
    super_admin_role = (
        db_session.query(RolesDbModel)
        .filter(RolesDbModel.name == "superAdmin")
        .one_or_none()
    )

    # Fetch user from the database and compare the role
    user_in_db = (
        db_session.query(UserDbModel).filter(UserDbModel.id == current_user.id).one_or_none()
    )
    if (
        user_in_db.role_id != super_admin_role.id
    ):  # Replace role_id with your actual attribute
        raise HTTPException(
            status_code=403, detail="Forbidden - Super Admin access required."
        )

    return current_user


async def admin_required(
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
):
    admin_role = (
        db_session.query(RolesDbModel).filter(RolesDbModel.name == "admin").one_or_none()
    )

    # Fetch user from the database and compare the role
    user_in_db = (
        db_session.query(UserDbModel).filter(UserDbModel.id == current_user.id).one_or_none()
    )

    if (
        user_in_db.role_id != admin_role.id
    ):  # Replace role_id with your actual attribute
        raise HTTPException(
            status_code=403, detail="Forbidden - Admin access required."
        )

    return current_user


async def super_admin_or_admin_required(
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
):
    admin_role_id, super_admin_role_id, _ = await get_role_ids(db_session=db_session)

    user_in_db = db_session.query(UserDbModel).filter(UserDbModel.id == current_user.id).one_or_none()

    if user_in_db.role_id in {admin_role_id, super_admin_role_id}:
        return current_user
    else:
        raise HTTPException(status_code=403, detail="Access denied.")


async def end_user_required(
    current_user: User = Depends(
        get_current_user_from_token
    ),  # Optional dependency injection
    db_session: SessionLocal = Depends(Database().get_db),
):
    # Fetch cached role IDs
    _, _, end_user_role_id = await get_role_ids(db_session=db_session)

    # Fetch user from the database and compare the role
    user_in_db = await db_session.query(
        UserDbModel.select().where(
            UserDbModel.c.id == current_user.id
        )  # replace id with correct attribute name
    ).one_or_none()

    if (
        user_in_db.role_id != end_user_role_id
    ):  # Replace role_id with your actual attribute
        raise HTTPException(
            status_code=403, detail="Forbidden - end user access required."
        )

    return current_user


async def is_super_admin(
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
) -> bool:
    super_admin_role = (
        db_session.query(RolesDbModel).filter(RolesDbModel.name == "superAdmin").one_or_none()
    )

    # Fetch user from the database and compare the role
    user_in_db = (
        db_session.query(UserDbModel).filter(UserDbModel.id == current_user.id).one_or_none()
    )

    if (
        user_in_db.role_id == super_admin_role.id
    ):  # Replace role_id with your actual attribute
        return True

    return False


async def is_admin(
    current_user: User = Depends(get_current_user_from_token),
    db_session: SessionLocal = Depends(Database().get_db),
) -> bool:
    admin_role = await db_session.query(
        RolesDbModel.select().where(RolesDbModel.c.name == "admin")
    ).one_or_none()

    # Fetch user from the database and compare the role
    user_in_db = await db_session.query(
        UserDbModel.select().where(
            UserDbModel.c.id == current_user.id
        )  # replace id with correct attribute name
    ).one_or_none()

    if (
        user_in_db.role_id == admin_role.id
    ):  # Replace role_id with your actual attribute
        return True

    return False


async def is_end_user(
    current_user: User = Depends(
        get_current_user_from_token
    ),  # Optional dependency injection
    db_session: SessionLocal = Depends(Database().get_db),
) -> bool:
    end_user_role = db_session.query(
        RolesDbModel.select().where(RolesDbModel.c.name == "endUser")
    ).one_or_none()

    # Fetch user from the db_session and compare the role
    user_in_db = db_session.query(
        UserDbModel.select().where(UserDbModel.c.id == current_user.id)
    ).one_or_none()

    if (
        user_in_db.role_id == end_user_role.id
    ):  # Replace role_id with your actual attribute
        return True

    return False
