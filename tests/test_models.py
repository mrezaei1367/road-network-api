import pytest
from sqlalchemy.exc import IntegrityError

from app import models


def test_customer_model_fields(db):
    customer = models.Customer(name="TestCustomer", api_key="testapikey")
    db.add(customer)
    db.commit()

    result = db.query(models.Customer).first()
    assert result.name == "TestCustomer"
    assert result.api_key == "testapikey"


def test_unique_customer_name_and_api_key(db):
    c1 = models.Customer(name="Test", api_key="key1")
    db.add(c1)
    db.commit()

    c2 = models.Customer(name="Test", api_key="key2")
    db.add(c2)
    with pytest.raises(IntegrityError):
        db.commit()


def test_road_network_unique_constraint(db):
    customer = models.Customer(name="CustomerA", api_key="key123")
    db.add(customer)
    db.commit()

    rn1 = models.RoadNetwork(customer_id=customer.id, name="netA", version="1.0")
    db.add(rn1)
    db.commit()

    rn2 = models.RoadNetwork(customer_id=customer.id, name="netA", version="1.0")
    db.add(rn2)
    with pytest.raises(IntegrityError):
        db.commit()


def test_road_edge_insert_and_relationship(db):
    customer = models.Customer(name="EdgeCustomer", api_key="edgekey")
    db.add(customer)
    db.commit()

    network = models.RoadNetwork(customer_id=customer.id, name="EdgeNet", version="1.0")
    db.add(network)
    db.commit()

    edge = models.RoadEdge(
        network_id=network.id,
        properties={"speed": 50},
        geometry="LINESTRING(0 0, 1 1)",
        is_current=True,
    )
    db.add(edge)
    db.commit()

    result = db.query(models.RoadEdge).first()
    assert result.network_id == network.id
    assert result.properties["speed"] == 50
    assert result.is_current is True
