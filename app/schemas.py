from datetime import datetime
from typing import Any, Dict, List

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


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    properties: Dict[str, Any]
    geometry: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
