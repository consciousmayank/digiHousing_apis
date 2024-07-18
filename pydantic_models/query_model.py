from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class QueryTypeEnum(str, Enum):
    Buy_a_home = "Buy_a_home"
    Rent_a_home = "Rent_a_home"
    Sell_a_home = "Sell_a_home"

class QueryModel(BaseModel):
    user_phonenumber: str
    user_name: str
    query_type: QueryTypeEnum
    property_type_id: int
    property_config_id: int
    property_address_id: Optional[int] = None
    contacted: Optional[bool] = False
    resolution: Optional[str] = ''
    amenities_id: Optional[int] = None

    

class QueryList(QueryModel):
    id: int    

class QueryStatusUpdate(BaseModel):
    contacted: bool
    resolution: str