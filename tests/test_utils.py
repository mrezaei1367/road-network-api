import io
import json

import pytest
from fastapi import HTTPException
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, shape

from app.utils import (
    extract_network_info,
    geojson_to_road_edges,
    load_geojson_file,
    road_edges_to_geojson,
)


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


def test_geojson_to_road_edges_valid():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": 1},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[0, 0], [1, 1]],
                },
            }
        ],
    }

    road_network_id = 123
    geometry = from_shape(shape(geojson["features"][0]["geometry"]), srid=4326)
    edges = geojson_to_road_edges(geojson, road_network_id)
    assert len(edges) == 1
    assert edges[0]["network_id"] == road_network_id
    assert edges[0]["properties"] == {"id": 1}
    assert geometry == edges[0]["geometry"]


def test_geojson_to_road_edges_empty_features():
    geojson = {"type": "FeatureCollection", "features": []}
    edges = geojson_to_road_edges(geojson, 1)
    assert edges == []


def test_road_edges_to_geojson():
    shapely_geom = LineString([(0, 0), (1, 1)])
    mock_edge = MockRoadEdge(
        properties={"name": "Test Road"},
        geometry=from_shape(shapely_geom, srid=4326),
    )
    geojson = road_edges_to_geojson([mock_edge])
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1
    feature = geojson["features"][0]
    assert feature["geometry"]["type"] == "LineString"
    assert feature["properties"]["name"] == "Test Road"
