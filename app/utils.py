import json
import logging
import re
from typing import List

from fastapi import HTTPException, status
from shapely.geometry import shape

logger = logging.getLogger(__name__)


def geojson_to_road_edges(geojson_data: dict, network_id: int) -> List[dict]:
    features = geojson_data.get("features", [])
    edges = []

    for feature in features:
        geometry = shape(feature["geometry"])
        properties = feature.get("properties", {})

        edge = {
            "network_id": network_id,
            "properties": properties,
            "geometry": geometry.wkt,
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
