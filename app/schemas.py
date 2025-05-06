from datetime import datetime

from pydantic import BaseModel


class RoadNetworkObject(BaseModel):
    name: str
    geojson: dict
    version: str = "1.0"


class RoadNetworkResponse(BaseModel):
    id: int
    name: str
    version: str
    upload_time: datetime


class CustomerCreate(BaseModel):
    name: str


class CustomerResponse(BaseModel):
    id: int
    name: str
    api_key: str
