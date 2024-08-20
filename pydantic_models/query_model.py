from enum import Enum
from typing import List, Optional

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
    address: Optional[dict] = None
    contacted: Optional[bool] = False
    resolution: Optional[str] = ''
    amenities: Optional[List[int]] = None  # Changed from amenities_id to amenities_ids

class AmenityModel(BaseModel):
    id: int
    name: str
    description: str

class QueryList(BaseModel):
    id: int
    user_phonenumber: str
    user_name: str
    query_type: QueryTypeEnum
    property_type_id: int
    property_config_id: int
    property_address_id: Optional[int] = None
    contacted: bool
    resolution: str
    amenities: List[AmenityModel]  # Add this line to include amenities in the response

class QueryStatusUpdate(BaseModel):
    contacted: bool
    resolution: str