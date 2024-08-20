import enum

from sqlalchemy import (TIMESTAMP, Boolean, Column, ForeignKey, Integer,
                        String, Table, func)
from sqlalchemy.orm import relationship

from database.database_connection import Base

# an association table for the many-to-many relationship. 
# Association table query_amenities to represent the many-to-many relationship 
# between queries and amenities.
query_amenities = Table('query_amenities', Base.metadata,
    Column('query_id', Integer, ForeignKey('queries.id')),
    Column('amenity_id', Integer, ForeignKey('amenities.id'))
)


class QueryTypeEnum(enum.Enum):
    Buy_a_home = "Buy_a_home"
    Rent_a_home = "Rent_a_home"
    Sell_a_home = "Sell_a_home"
    
class RolesDbModel(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    users = relationship("UserDbModel", back_populates="role")


class UserDbModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email_id = Column(String, unique=True)
    password = Column(String)
    verification_code = Column(String, default=None)
    confirmed = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    role = relationship("RolesDbModel", back_populates="users")
    property_types = relationship("PropertyTypesDbModel", back_populates="user")
    property_config = relationship("PropertyConfigDbModel", back_populates="user")
    property_address = relationship("PropertyAddressDbModel", back_populates="user")
    amenities = relationship("AmenitiesDbModel", back_populates="user")
    audit_logs = relationship("AuditLogsDbModel", back_populates="user")

    def to_dict_name_role(self):
        return {
            "id": self.id,
            "email id": self.email_id,
            "role": self.role.name
        }

class PropertyTypesDbModel(Base):
    __tablename__ = 'property_types'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_by_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    user = relationship("UserDbModel", back_populates="property_types")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by_user": self.user.email_id,
        }

class PropertyConfigDbModel(Base):
    __tablename__ = 'property_config'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_by_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    user = relationship("UserDbModel", back_populates="property_config")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by_user": self.user.email_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_dict_for_queries(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by_user": self.user.email_id,
        }

class PropertyAddressDbModel(Base):
    __tablename__ = 'property_address'
    id = Column(Integer, primary_key=True, index=True)
    house_no = Column(String)
    building_name = Column(String)
    street = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    zip_code = Column(String(length=6), nullable=False)
    created_by_user = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    user = relationship("UserDbModel", back_populates="property_address")

    def to_dict(self):
        return {
            "id": self.id,
            "house_no": self.house_no,
            "building_name": self.building_name,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "zip_code": self.zip_code,
            "created_by_user": self.user.email_id,
        }

class AmenitiesDbModel(Base):
    __tablename__ = 'amenities'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_by_user = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    user = relationship("UserDbModel", back_populates="amenities")
    # relationship that references back to QueriesDbModel.
    queries = relationship("QueriesDbModel", secondary=query_amenities, back_populates="amenities")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by_user": self.user.email_id,
        }

class QueriesDbModel(Base):
    __tablename__ = 'queries'
    id = Column(Integer, primary_key=True, index=True)
    user_phonenumber = Column(String(length=10), nullable=False)
    user_name = Column(String, nullable=False)
    query_type = Column(String, nullable=False)
    property_type_id = Column(Integer, ForeignKey("property_types.id"), nullable=False)
    property_config_id = Column(Integer, ForeignKey("property_config.id"), nullable=False)
    property_address_id = Column(Integer, ForeignKey("property_address.id"), nullable=True)
    contacted = Column(Boolean, default=False)
    resolution = Column(String, default=None)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    property_type = relationship("PropertyTypesDbModel")
    property_config = relationship("PropertyConfigDbModel")
    property_address = relationship("PropertyAddressDbModel")
    # relationship that uses the query_amenities association table.
    amenities = relationship("AmenitiesDbModel", secondary=query_amenities, back_populates="queries")

    def to_dict(self):
        return {
            "id": self.id,
            "user_phonenumber": self.user_phonenumber,
            "user_name": self.user_name,
            "query_type": self.query_type,
            "contacted": self.contacted,
            "resolution": self.resolution,
            "property_type_id": self.property_type_id,
            "property_config_id": self.property_config_id,
            "property_address_id": self.property_address_id,
            "amenities": [amenity.to_dict() for amenity in self.amenities],
            "property_type": self.property_type.to_dict() if self.property_type else None,
            "property_config": self.property_config.to_dict_for_queries() if self.property_config else None,
            "property_address": self.property_address.to_dict() if self.property_address else None,
        }


class AuditLogsDbModel(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, nullable=False)
    record_id = Column(Integer, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    old_values = Column(String, nullable=False)
    new_values = Column(String, nullable=False)
    timestamp = Column(TIMESTAMP, default=func.now(), nullable=False)
    user = relationship("UserDbModel", back_populates="audit_logs")
    def to_dict(self):
        return {
            "id": self.id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "changed_by": self.user.email_id,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

class ImagesDbModel(Base):
    __tablename__ = 'images'
    key = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())



# # Adding amenities to a query
# query = QueriesDbModel(...)
# amenity1 = AmenitiesDbModel(...)
# amenity2 = AmenitiesDbModel(...)
# query.amenities.extend([amenity1, amenity2])

# # Removing an amenity from a query
# query.amenities.remove(amenity1)
