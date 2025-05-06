import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Customer, RoadEdge, RoadNetwork

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@db:5432/road_network"
)

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def customer(db):
    customer = Customer(name="Test", api_key="testkey")
    db.add(customer)
    db.commit()
    db.refresh(customer)
    yield customer


@pytest.fixture
def road_network(db, customer):
    road_network = RoadNetwork(
        name="testnet",
        version="1.0",
        customer_id=customer.id,
        upload_time="2025-01-01 10:30:00",
    )
    db.add(road_network)
    db.commit()
    db.refresh(road_network)

    edge = RoadEdge(
        network_id=road_network.id,
        properties={"name": "Test Road"},
        geometry="LINESTRING(0 0, 1 1)",
        is_current=True,
        valid_from="2025-01-01 10:30:00",
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    yield road_network
