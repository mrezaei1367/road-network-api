from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False)


class RoadNetwork(Base):
    __tablename__ = "road_networks"
    __table_args__ = (
        UniqueConstraint(
            "customer_id", "name", "version", name="uq_customer_name_version"
        ),
    )
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    upload_time = Column(TIMESTAMP(timezone=True), server_default=func.now())


class RoadEdge(Base):
    __tablename__ = "road_edges"

    id = Column(Integer, primary_key=True, index=True)
    network_id = Column(
        Integer, ForeignKey("road_networks.id"), nullable=False, index=True
    )
    properties = Column(JSON)
    geometry = Column(Geometry("LINESTRING", srid=4326))
    is_current = Column(Boolean, default=True)
    valid_from = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    valid_to = Column(TIMESTAMP(timezone=True), index=True)
