import json
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape

if TYPE_CHECKING:
    from .models import RoadEdge


logger = logging.getLogger(__name__)


def geojson_to_road_edges(geojson_data: dict, network_id: int) -> list[dict]:
    features = geojson_data.get("features", [])
    edges = []

    for feature in features:
        properties = feature.get("properties", {})
        geometry = from_shape(shape(feature["geometry"]), srid=4326)

        edge = {
            "network_id": network_id,
            "properties": properties,
            "geometry": geometry,
            "valid_from": datetime.now(),
        }
        edges.append(edge)

    return edges


def extract_network_info(filename: str) -> tuple:
    match = re.match(r"^road_network_([a-zA-Z0-9_]+)_(\d+\.\d+)\.geojson$", filename)
    if not match:
        logger.warning(
            "Filename format is invalid: %s. Expected format: road_network_<name>_<version>.geojson",
            filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename format is invalid. Expected format: road_network_<name>_<version>.geojson",
        )
    name = match.group(1)
    version = match.group(2)
    return name, version


def load_geojson_file(file) -> dict:
    try:
        geojson_data = json.load(file)
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from the uploaded file")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid GeoJSON file",
        )
    return geojson_data


def road_edges_to_geojson(edges: list["RoadEdge"]) -> dict:
    features = []

    for edge in edges:
        geom = to_shape(edge.geometry)
        features.append(
            {
                "type": "Feature",
                "properties": edge.properties,
                "geometry": mapping(geom),  # Convert Shapely to GeoJSON
            }
        )

    return {"type": "FeatureCollection", "features": features}
