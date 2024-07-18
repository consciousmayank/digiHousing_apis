from pydantic import BaseModel


class User(BaseModel):
    email: str


class UserIn(User):
    password: str

class UserUpdate(User):
    id: int

class UserInWithRole(UserIn):
    role_id: int
