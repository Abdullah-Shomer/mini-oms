# Mini OMS

A small order-management system built with Python and FastAPI for managing products through a CLI or REST API.

## Features

- Add products
- List all products
- Find products by SKU
- Update product quantities
- Delete products
- Prevent duplicate SKUs
- Reject negative prices and quantities
- Automated business-logic and API tests

## Technologies

- Python
- FastAPI
- Pydantic
- Uvicorn
- Pytest
- HTTPX

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the API

```bash
python -m uvicorn api:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API information |
| GET | `/products` | List all products |
| POST | `/products` | Create a product |
| GET | `/products/{sku}` | Find a product by SKU |
| PATCH | `/products/{sku}/quantity` | Update product quantity |
| DELETE | `/products/{sku}` | Delete a product |

## Run the CLI

```bash
python app.py
```

## Run the Tests

```bash
python -m pytest
```

The project includes tests for the product business logic and FastAPI endpoints.

## Current Storage

Products are currently stored in memory. Data is reset whenever the API server restarts. Database persistence can be added in a future version.