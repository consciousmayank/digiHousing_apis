from pydantic import BaseModel


class Role(BaseModel):
    name: str


class RoleUpdate(Role):
    id: int

