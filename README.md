# Road Network Management API

A REST API for managing road network data in GeoJSON format with versioning support.

## Features

- Upload new road networks (GeoJSON)
- Update existing road networks while preserving history
- Retrieve road networks with versioning support
- Customer-based authentication via API keys

## Technologies

- FastAPI
- PostgreSQL with PostGIS
- Docker

## Setup

1. Clone the repository
2. Run `docker-compose up app`
3. The API will be available at `http://localhost:8000`

## API Documentation

After starting the service, visit `http://localhost:8000/docs` for interactive API documentation.

### Endpoints

#### Create Customer
- `POST /api/customers/`
  - Creates a new customer and returns an API key
  - Request body: `{"name": "Customer Name"}`

#### Upload Road Network
- `POST /api/road-networks/`
  - Uploads a new road network
  - Headers: `X-API-Key: <your_api_key>`
  - form 'file=@"/file_directory/road_network_bayrischzell_1.0.geojson"'
  

#### Update Road Network
- `PUT /api/road-networks/{road_network_name}`
  - Updates an existing road network (creates new version)
  - Headers: `X-API-Key: <your_api_key>`
  - form 'file=@"/file_directory/road_network_bayrischzell_1.0.geojson"'


#### Get Road Network
- `GET /api/road-networks/{road_network_name}`
  - Retrieves a road network in GeoJSON format
  - Headers: `X-API-Key: <your_api_key>`
  - Optional query parameter: `query_time` (e.g., `?query_time=2025-05-03%2021:44:41`)

## Data Model

The solution uses a versioned data model where:
- Each road network update creates a new version
- Previous edges are marked as not current but remain in the database
- All queries return only current edges unless a specific time is requested

## Example Usage

1. Create a customer:
```bash
curl -X POST "http://localhost:8000/api/customers/" \
-H "Content-Type: application/json" \
-d '{
    "name": "Test Customer"
  }'
```
Then You can use the value of the api_key that you get from the output, in the header of other APIs like following. 

2. Upload a new road network
```bash
curl -X POST "http://localhost:8000/api/road-networks/" \
-H "x-api-key: fKJVI7cKyZcnNi4ETWlCQyour_api_keyMqBwcmaIScOw9w3k7dX21c" \
-F "file=@/Users/user_name/Documents/geo_json_data/road_network_bayrischzell_1.0.geojson"
```

3. Update an existing road network
```bash
curl -X PUT "http://localhost:8000/api/road-networks/bayrischzell" \
-H "x-api-key: your_api_key" \
-F "file=@/Users/user_name/Documents/geo_json_data/road_network_bayrischzell_1.1.geojson"
```

4. Get a road network by name or get a specific version of a road network with using a specific time.
```bash
curl -X GET "http://localhost:8000/api/road-networks/bayrischzell" \
-H "x-api-key: your_api_key"

curl -X GET "http://localhost:8000/api/road-networks/bayrischzell?query_time=2025-05-05%2021:49:27.51" \
-H "x-api-key: your_api_key"
```

## Test
For executing the unit tests you just neet to:
Run `docker-compose up --build tests`
