import logging

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .crud import (
    create_customer,
    create_road_network,
    get_customer_by_api_key,
    get_network_by_name_time,
    mark_previous_edges_as_old,
)
from .database import engine, get_db
from .models import Base
from .schemas import (
    CustomerCreate,
    CustomerResponse,
    RoadNetworkObject,
    RoadNetworkResponse,
)
from .utils import extract_network_info, load_geojson_file

logger = logging.getLogger(__name__)
app = FastAPI()

# Initialize database
Base.metadata.create_all(bind=engine)


@app.post("/api/customers/", response_model=CustomerResponse)
def add_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    try:
        return create_customer(db, customer)
    except IntegrityError as e:
        if "customers_name_key" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer with this name already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error occurred",
        )


@app.post(
    "/api/road-networks/",
    response_model=RoadNetworkResponse,
    summary="Upload a new road network",
)
def upload_network(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    customer = get_customer_by_api_key(db, x_api_key)
    name, version = extract_network_info(file.filename)

    existing_network = get_network_by_name_time(db, customer.id, name)
    if existing_network:
        logger.warning(
            "Road network %s already exists for customer %s", name, customer.id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Road network already exists. Use PUT to update.",
        )
    geojson_data = load_geojson_file(file.file)
    road_network = RoadNetworkObject(name=name, geojson=geojson_data, version=version)
    return create_road_network(db, road_network, customer.id)


@app.put(
    "/api/road-networks/{road_network_name}",
    response_model=RoadNetworkResponse,
    summary="Update an existing road network",
)
def update_network(
    road_network_name: str,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    customer = get_customer_by_api_key(db, x_api_key)
    name, version = extract_network_info(file.filename)
    if name != road_network_name:
        logger.warning(
            "Road network name in the file (%s) does not match the requested name (%s)",
            name,
            road_network_name,
        )
        raise HTTPException(
            status_code=400,
            detail="Road network name in the file does not match the requested name",
        )

    existing_network = get_network_by_name_time(db, customer.id, road_network_name)
    if not existing_network:
        logger.warning(
            "Road network %s not found for customer %s", road_network_name, customer.id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Road network not found"
        )
    if existing_network.version == version:
        logger.warning(
            "Road network %s with version %s already exists for customer %s",
            road_network_name,
            version,
            customer.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Road network with this version already exists. Use a different version.",
        )
    mark_previous_edges_as_old(db, existing_network.id)
    geojson_data = load_geojson_file(file.file)
    road_network = RoadNetworkObject(
        name=road_network_name, geojson=geojson_data, version=version
    )
    return create_road_network(db, road_network, customer.id)
