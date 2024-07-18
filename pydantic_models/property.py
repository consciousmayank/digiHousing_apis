import datetime
from typing import Optional

from pydantic import BaseModel

from pydantic_models.user_model import User


class PropertyType(BaseModel):
    name: str
    description: Optional[str] 

class PropertyTypeList(PropertyType):
    id: int
    created_by_user: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

class PropertyTypeUpdate(PropertyType):
    id: int
    name: str
    description: Optional[str]     
    created_by_user: int
    created_at: datetime.datetime
    edited_at: datetime.datetime


class PropertyConfig(BaseModel):
    name: str
    description: Optional[str]

class PropertyConfigList(PropertyConfig):
    id: int
    created_by_user: User
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
class PropertyAddress(BaseModel):
    house_no: Optional[str]
    building_name: Optional[str]
    street: Optional[str]
    city: str
    state: str
    country: str
    zip_code: str
    created_by_user: int
    
class Amenity(BaseModel):
    name: str
    description: Optional[str]
    created_by_user: int