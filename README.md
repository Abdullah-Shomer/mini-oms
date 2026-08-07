# Mini OMS

A production-style order management backend built with FastAPI and PostgreSQL.

Mini OMS manages products, inventory, users, and orders. It includes transactional stock updates, JWT authentication, role-based authorization, database migrations, automated testing, continuous integration, Docker deployment, and a live cloud database.

## Live Application

- API: https://mini-oms-api.onrender.com
- Interactive Swagger documentation: https://mini-oms-api.onrender.com/docs
- Health check: https://mini-oms-api.onrender.com/health

The API runs on Render’s free service tier, so the first request after inactivity may take longer while the service wakes up.

## Features

### Product Management

- Create products with unique SKUs
- Retrieve one product by SKU
- List products with pagination
- Search products by name or SKU
- Update inventory quantities
- Delete products
- Reject negative prices and quantities
- Trim and validate product names and SKUs

### Order Management

- Create orders containing one or more products
- Prevent duplicate SKUs within an order
- Reject missing products and insufficient inventory
- Deduct inventory atomically when an order is created
- Preserve the product price at the time of purchase
- Retrieve individual orders and order history
- Cancel orders safely
- Restore inventory exactly once when an order is cancelled

### Authentication and Authorization

- Register users
- Hash passwords with Argon2
- Authenticate with OAuth2 password flow
- Issue and validate JWT access tokens
- Support `admin` and `operator` roles
- Restrict product mutations to administrators
- Require authentication for order creation and cancellation
- Prevent password hashes from appearing in API responses

### Reliability and Delivery

- PostgreSQL persistence
- SQLAlchemy ORM and repository layer
- Alembic database migrations
- Row locking during order creation
- Transaction rollback on business-rule failures
- Database constraints for critical invariants
- Isolated PostgreSQL integration tests
- Ruff formatting and lint checks
- GitHub Actions continuous integration
- Docker image running as a non-root user
- Docker Compose configuration with health checks
- Database-backed application health endpoint
- Cloud deployment using Render and Neon PostgreSQL

## Technology Stack

- Python 3.9
- FastAPI
- Pydantic
- SQLAlchemy 2
- PostgreSQL
- Psycopg 3
- Alembic
- PyJWT
- pwdlib with Argon2
- Pytest
- Ruff
- Docker and Docker Compose
- GitHub Actions
- Render
- Neon PostgreSQL

## Architecture

The application separates HTTP behavior from database operations:

```text
Client
  |
  v
FastAPI endpoints and validation
  |
  v
Repository layer and business transactions
  |
  v
SQLAlchemy ORM
  |
  v
PostgreSQL
```

Main responsibilities:

- `api.py` defines request models, authentication dependencies, authorization rules, and HTTP endpoints.
- `product_repository.py` handles product persistence.
- `order_repository.py` handles transactional order creation, cancellation, and inventory changes.
- `user_repository.py` handles user persistence and authentication.
- `security.py` handles password hashing and JWT operations.
- `models.py` defines SQLAlchemy database models and constraints.
- `database.py` configures the SQLAlchemy engine and database sessions.
- `config.py` validates environment-based configuration.
- `migrations/` contains Alembic schema migrations.
- `conftest.py` provides isolated database fixtures for integration tests.

## Important Design Decisions

### Transactional Order Creation

Order creation locks each selected product row with `SELECT ... FOR UPDATE`. This prevents concurrent orders from reading and spending the same inventory simultaneously.

The product checks, inventory deduction, order creation, and order-item creation run in one transaction. If any item is missing or has insufficient stock, the transaction rolls back and no partial order is saved.

### Historical Unit Prices

Each order item stores its own `unit_price`. Product prices may change later, but existing orders retain the price charged when they were created.

### Safe Cancellation

Cancelling an order restores its inventory within a transaction. A cancelled order cannot be cancelled again, preventing stock from being restored twice.

### Layered Validation

Business rules are protected at multiple levels:

- Pydantic validates incoming API data.
- Repository functions enforce transactional business behavior.
- PostgreSQL constraints protect stored data.
- Automated tests verify API responses and database state.

### Role-Based Authorization

Public registration creates an `operator`. Administrative privileges cannot be requested through the registration payload. Admin-only dependencies protect product creation, quantity updates, and deletion.

## API Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/` | Public | API information |
| `GET` | `/health` | Public | Verify API and database health |
| `GET` | `/products` | Public | List, paginate, and search products |
| `POST` | `/products` | Admin | Create a product |
| `GET` | `/products/{sku}` | Public | Retrieve a product |
| `PATCH` | `/products/{sku}/quantity` | Admin | Set product quantity |
| `DELETE` | `/products/{sku}` | Admin | Delete a product |
| `POST` | `/orders` | Authenticated | Create an order and deduct inventory |
| `GET` | `/orders` | Public | List orders |
| `GET` | `/orders/{order_id}` | Public | Retrieve an order |
| `POST` | `/orders/{order_id}/cancel` | Authenticated | Cancel an order and restore inventory |
| `POST` | `/auth/register` | Public | Register an operator account |
| `POST` | `/auth/token` | Public | Authenticate and receive a JWT |
| `GET` | `/auth/me` | Authenticated | Retrieve the current user |

## Configuration

Copy the example configuration:

```bash
cp .env.example .env
```

Local development uses separate database settings:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mini_oms
DB_USER=mini_oms_user
DB_PASSWORD=replace-me
```

Cloud deployments can use a single SQLAlchemy-compatible connection string:

```text
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
```

Authentication settings:

```text
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Never commit `.env` or real credentials.

## Local Development

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create the PostgreSQL databases required for development and testing, then apply migrations:

```bash
alembic upgrade head
DB_NAME=mini_oms_test alembic upgrade head
```

Start the API:

```bash
python -m uvicorn api:app --reload
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

## Docker

Build and start the API with PostgreSQL:

```bash
docker compose up --build -d
```

Check service health:

```bash
docker compose ps
curl http://127.0.0.1:8000/health
```

Stop the containers:

```bash
docker compose down
```

The named PostgreSQL volume preserves local container data between restarts. To deliberately remove that development data:

```bash
docker compose down -v
```

## Database Migrations

Create a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe the schema change"
```

Review the generated migration before applying it:

```bash
alembic upgrade head
```

Alembic also runs when the deployed Docker container starts, ensuring the cloud database reaches the expected schema version.

## Quality Checks

Format the project:

```bash
ruff format .
```

Run lint checks:

```bash
ruff check .
```

Run the complete test suite:

```bash
python -m pytest
```

The project currently contains 63 automated tests covering product logic, API behavior, validation, database persistence, transactions, authentication, authorization, JWT handling, pagination, search, and health checks.

## Continuous Integration

GitHub Actions runs on pull requests and pushes to `main`. The pipeline:

1. Starts PostgreSQL
2. Installs dependencies
3. Applies Alembic migrations
4. Checks formatting
5. Runs Ruff lint checks
6. Runs the complete Pytest suite

Code is merged only after the automated checks pass.

## Deployment

The production API is packaged with Docker and deployed to Render. Production data is stored in Neon PostgreSQL.

The container:

- Runs as a non-root user
- Reads secrets from environment variables
- Excludes `.env` from the image
- Applies database migrations before startup
- Binds to Render’s assigned port
- Exposes a database-backed `/health` endpoint

## Project Status

The agreed backend portfolio scope is complete and deployed.

Possible future improvements include refresh tokens, audit logs, structured logging, rate limiting, improved API error schemas, product-category support, order ownership rules, observability, performance testing, and a lightweight frontend.