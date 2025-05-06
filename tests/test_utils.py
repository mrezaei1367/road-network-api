import io
import json

import pytest
from fastapi import HTTPException
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString

from app.utils import extract_network_info, load_geojson_file


class MockRoadEdge:
    def __init__(self, properties, geometry):
        self.properties = properties
        self.geometry = geometry


def test_extract_network_info_valid():
    name, version = extract_network_info("road_network_highway_1.0.geojson")
    assert name == "highway"
    assert version == "1.0"


@pytest.mark.parametrize(
    "filename",
    [
        "roadnetwork_highway_1.0.geojson",
        "road_network_highway_v1.geojson",
        "road_network_.1.0.geojson",
        "invalid.geojson",
    ],
)
def test_extract_network_info_invalid(filename):
    with pytest.raises(HTTPException) as exc_info:
        extract_network_info(filename)
    assert exc_info.value.status_code == 400
    assert "Filename format is invalid" in exc_info.value.detail


def test_load_geojson_file_valid():
    valid_geojson = io.StringIO(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [],
            }
        )
    )
    data = load_geojson_file(valid_geojson)
    assert data["type"] == "FeatureCollection"
    assert isinstance(data["features"], list)


def test_load_geojson_file_invalid():
    invalid_json = io.StringIO("not valid json")
    with pytest.raises(HTTPException) as exc_info:
        load_geojson_file(invalid_json)
    assert exc_info.value.status_code == 400
    assert "not a valid GeoJSON file" in exc_info.value.detail
