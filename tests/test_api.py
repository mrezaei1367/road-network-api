import io
import json
from unittest.mock import patch

from fastapi import status

from app.models import Customer, RoadEdge, RoadNetwork

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
