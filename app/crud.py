import logging
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from . import models, schemas
from .utils import geojson_to_road_edges, road_edges_to_geojson

logger = logging.getLogger(__name__)


def get_customer_by_api_key(db: Session, api_key: str) -> models.Customer:
    if api_key is None:
        logger.warning("API key is missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key is required"
        )
    customer = (
        db.query(models.Customer).filter(models.Customer.api_key == api_key).first()
    )
    if not customer:
        logger.warning("Invalid API key: %s", api_key)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
        )
    return customer


def create_road_network(
    db: Session, road_network: schemas.RoadNetworkObject, customer_id: int
) -> schemas.RoadNetworkResponse:

    db_network = models.RoadNetwork(
        customer_id=customer_id,
        name=road_network.name,
        version=road_network.version,
    )
    db.add(db_network)
    db.commit()
    db.refresh(db_network)

    # Add edges
    edges = geojson_to_road_edges(road_network.geojson, db_network.id)

    road_edges = [models.RoadEdge(**edge) for edge in edges]
    db.bulk_save_objects(road_edges)
    db.commit()

    return schemas.RoadNetworkResponse(
        id=db_network.id,
        name=db_network.name,
        version=db_network.version,
        upload_time=db_network.upload_time,
    )


def get_network_by_name_time(
    db: Session, customer_id: int, name: str, query_time: datetime = None
) -> models.RoadNetwork:
    query = db.query(models.RoadNetwork).filter(
        and_(
            models.RoadNetwork.customer_id == customer_id,
            models.RoadNetwork.name == name,
        )
    )
    if query_time:
        # Get the latest version before the specified query_time
        road_network = (
            query.filter(models.RoadNetwork.upload_time <= query_time)
            .order_by(models.RoadNetwork.upload_time.desc())
            .first()
        )
    else:
        road_network = query.order_by(models.RoadNetwork.upload_time.desc()).first()
    return road_network


def create_customer(
    db: Session, customer: schemas.CustomerCreate
) -> schemas.CustomerResponse:
    api_key = secrets.token_urlsafe(32)

    db_customer = models.Customer(name=customer.name, api_key=api_key)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return schemas.CustomerResponse(
        id=db_customer.id, name=db_customer.name, api_key=db_customer.api_key
    )


def mark_previous_edges_as_old(db: Session, network_id: int) -> None:
    db.query(models.RoadEdge).filter(
        and_(
            models.RoadEdge.network_id == network_id, models.RoadEdge.is_current == True
        )
    ).update({"is_current": False, "valid_to": datetime.now(timezone.utc)})
    db.commit()


def get_edges_for_network(
    db: Session,
    network_id: int,
    query_time: datetime = None,
) -> dict:

    edges = db.query(models.RoadEdge).filter(models.RoadEdge.network_id == network_id)
    if query_time:
        # Get edges valid at the specified time
        edges = edges.filter(
            and_(
                models.RoadEdge.valid_from <= query_time,
                or_(
                    models.RoadEdge.valid_to >= query_time,
                    models.RoadEdge.valid_to.is_(None),
                ),
            )
        ).all()
    else:
        edges = edges.filter(models.RoadEdge.is_current == True).all()
    if not edges:
        logger.warning(
            "No edges found for road network %s at time %s", network_id, query_time
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No edges found for the specified road network",
        )

    return road_edges_to_geojson(edges)
