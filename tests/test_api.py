import io
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

from app.crud import create_road_network
from app.models import Customer, RoadEdge, RoadNetwork
from app.schemas import RoadNetworkObject

geojson_content = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Test Road"},
            "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
        }
    ],
}

updated_geojson_content = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Updated Test Road"},
            "geometry": {"type": "LineString", "coordinates": [[0, 0], [2, 2]]},
        }
    ],
}


@pytest.fixture
def mock_logger(monkeypatch):
    logger = MagicMock()
    monkeypatch.setattr("app.main.logger", logger)
    return logger


# --- POST /api/customers/ ---
def test_create_customer(client, db):
    response = client.post("/api/customers/", json={"name": "Test Customer"})
    customer = db.query(Customer).filter(Customer.name == "Test Customer").first()
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Test Customer"
    assert customer is not None
    assert customer.api_key is not None
    assert customer.api_key == response.json()["api_key"]


# --- POST /api/road-networks/ ---
@patch("app.utils.load_geojson_file", return_value=geojson_content)
def test_upload_network(mock_load_geojson, client, db, customer):
    geojson_file = io.BytesIO(json.dumps(geojson_content).encode("utf-8"))
    files = {
        "file": ("road_network_testnet_1.0.geojson", geojson_file, "application/json")
    }
    response = client.post(
        "/api/road-networks/", headers={"x-api-key": customer.api_key}, files=files
    )
    road_network = db.query(RoadNetwork).filter(RoadNetwork.name == "testnet").first()
    edges = db.query(RoadEdge).filter(RoadEdge.network_id == road_network.id).all()
    assert response.status_code == status.HTTP_200_OK
    assert road_network is not None
    assert response.json()["name"] == road_network.name
    assert response.json()["version"] == road_network.version
    assert (
        road_network.upload_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        == response.json()["upload_time"]
    )
    assert len(edges) == 1
    assert edges[0].properties == {"name": "Test Road"}


# --- PUT /api/road-networks/{road_network_name} ---
@patch("app.utils.load_geojson_file", return_value=updated_geojson_content)
def test_update_network(mock_load_geojson, client, db, customer, road_network):
    updated_geojson_file = io.BytesIO(
        json.dumps(updated_geojson_content).encode("utf-8")
    )
    files = {
        "file": (
            "road_network_testnet_1.1.geojson",
            updated_geojson_file,
            "application/json",
        )
    }
    response = client.put(
        "/api/road-networks/testnet",
        headers={"x-api-key": customer.api_key},
        files=files,
    )
    updated_network = (
        db.query(RoadNetwork)
        .filter(RoadNetwork.name == "testnet")
        .order_by(RoadNetwork.upload_time.desc())
        .first()
    )
    edges = db.query(RoadEdge).filter(RoadEdge.network_id == updated_network.id).all()
    assert response.status_code == status.HTTP_200_OK
    assert updated_network is not None
    assert response.json()["name"] == updated_network.name
    assert response.json()["version"] == updated_network.version
    assert (
        updated_network.upload_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        == response.json()["upload_time"]
    )
    assert len(edges) == 1
    assert edges[0].properties == {"name": "Updated Test Road"}


@patch("app.utils.load_geojson_file", return_value=geojson_content)
def test_update_network_with_same_version(
    mock_load_geojson, client, db, customer, road_network
):
    geojson_file = io.BytesIO(json.dumps(geojson_content).encode("utf-8"))
    files = {
        "file": ("road_network_testnet_1.0.geojson", geojson_file, "application/json")
    }
    response = client.put(
        "/api/road-networks/testnet",
        headers={"x-api-key": customer.api_key},
        files=files,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Road network with this version already exists. Use a different version."
    )


# --- GET /api/road-networks/{road_network_name} ---
def test_get_network(client, db, customer, road_network):
    response = client.get(
        "/api/road-networks/testnet", headers={"x-api-key": customer.api_key}
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["features"]) == 1
    assert response.json()["features"][0]["properties"]["name"] == "Test Road"
    assert response.json()["features"][0]["geometry"]["coordinates"] == [[0, 0], [1, 1]]


def test_get_network_quey_time(client, db, customer, road_network):
    updated_network_obj = RoadNetworkObject(
        name="testnet", geojson=updated_geojson_content, version="1.1"
    )
    updated_network = create_road_network(db, updated_network_obj, customer.id)
    response = client.get(
        "/api/road-networks/testnet?query_time=2025-01-02 10:31:00",
        headers={"x-api-key": customer.api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["features"]) == 1
    assert response.json()["features"][0]["properties"]["name"] == "Test Road"
    assert response.json()["features"][0]["geometry"]["coordinates"] == [[0, 0], [1, 1]]


def test_get_network_not_found(client, db, customer):
    response = client.get(
        "/api/road-networks/nonexistent", headers={"x-api-key": customer.api_key}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Road network not found"


def test_get_network_invalid_api_key(client, db):
    response = client.get(
        "/api/road-networks/nonexistent", headers={"x-api-key": "invalid_key"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Invalid API key"


def test_get_network_invalid_query_time(client, customer, mock_logger):
    response = client.get(
        "/api/road-networks/testnet?query_time=invalid_time",
        headers={"x-api-key": customer.api_key},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "Invalid query time format. Use standard format like 'YYYY-MM-DD HH:MM:SS'"
    )
    assert mock_logger.warning.call_count == 1
    assert mock_logger.warning.call_args[0][0] == "Invalid query time format: %s"
