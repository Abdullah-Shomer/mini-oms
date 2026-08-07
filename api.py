from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from database import get_db
from models import User
from order_repository import (
    InsufficientStockError,
    OrderAlreadyCancelledError,
    OrderNotFoundError,
    ProductNotFoundError,
    cancel_order,
    create_order,
    find_order_by_id,
    list_orders,
)
from product_repository import create_product as create_product_in_db
from product_repository import delete_product as delete_product_from_db
from product_repository import find_product_by_sku as find_product_by_sku_in_db
from product_repository import list_products as list_products_from_db
from product_repository import update_product_quantity as update_quantity_in_db
from security import create_access_token, decode_access_token
from user_repository import authenticate_user
from user_repository import create_user as create_user_in_db
from user_repository import find_user_by_username as find_user_by_username_in_db

DatabaseSession = Annotated[Session, Depends(get_db)]
LoginForm = Annotated[OAuth2PasswordRequestForm, Depends()]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
AccessToken = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(
    token: AccessToken,
    db: DatabaseSession,
) -> User:
    username = decode_access_token(token)

    if username is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = find_user_by_username_in_db(db, username)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    quantity: int = Field(ge=0)

    @field_validator("name", "sku")
    @classmethod
    def validate_text_fields(cls, value: str):
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Name and SKU must not be blank")
        return cleaned_value


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    price: Decimal
    quantity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuantityUpdate(BaseModel):
    quantity: int = Field(ge=0)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Username must not be blank")
        return cleaned_value


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


app = FastAPI()


@app.get("/")
def root():
    message = {"message": "Mini OMS API"}

    return message


@app.get("/products", response_model=list[ProductResponse])
def list_products(
    db: DatabaseSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[Optional[str], Query(max_length=100)] = None,  # noqa: FA100
):
    return list_products_from_db(db, skip, limit, search)


@app.post(
    "/products",
    status_code=HTTP_201_CREATED,
    response_model=ProductResponse,
)
def create_new_product(
    product: ProductCreate,
    db: DatabaseSession,
    _admin: AdminUser,
):
    created_product = create_product_in_db(
        db,
        product.name,
        product.sku,
        product.price,
        product.quantity,
    )

    if created_product is None:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="Product with this SKU already exists",
        )

    return created_product


@app.get("/products/{sku}", response_model=ProductResponse)
def get_product(sku: str, db: DatabaseSession):
    found_product = find_product_by_sku_in_db(
        db,
        sku,
    )
    if found_product is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found")

    return found_product


@app.patch("/products/{sku}/quantity", response_model=ProductResponse)
def update_quantity(
    sku: str,
    update: QuantityUpdate,
    db: DatabaseSession,
    _admin: AdminUser,
):
    result = update_quantity_in_db(db, sku, update.quantity)

    if result is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found")
    return result


@app.delete("/products/{sku}")
def remove_product(
    sku: str,
    db: DatabaseSession,
    _admin: AdminUser,
):

    result = delete_product_from_db(db, sku)

    if result is False:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found")

    return {"message": "Product deleted successfully"}


class OrderItemCreate(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("SKU must not be blank")

        return cleaned_value


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_skus(self):
        skus = []

        for item in self.items:
            skus.append(item.sku)

        if len(skus) != len(set(skus)):
            raise ValueError("Each SKU may appear only once per order")

        return self


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


@app.post(
    "/orders",
    status_code=HTTP_201_CREATED,
    response_model=OrderResponse,
)
def create_new_order(
    order_data: OrderCreate,
    db: DatabaseSession,
    _current_user: CurrentUser,
):
    items = []

    for item in order_data.items:
        items.append((item.sku, item.quantity))

    try:
        return create_order(db, items)

    except ProductNotFoundError as error:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Product not found: {error}",
        ) from error

    except InsufficientStockError as error:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"Insufficient stock for SKU: {error}",
        ) from error


@app.get("/orders", response_model=list[OrderResponse])
def get_orders(db: DatabaseSession):
    return list_orders(db)


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: DatabaseSession):

    found_order = find_order_by_id(db, order_id)

    if found_order is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Order not found")
    return found_order


@app.post(
    "/orders/{order_id}/cancel",
    response_model=OrderResponse,
)
def cancel_existing_order(
    order_id: int,
    db: DatabaseSession,
    _current_user: CurrentUser,
):
    try:
        return cancel_order(db, order_id)

    except OrderNotFoundError as error:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Order not found: {error}",
        ) from error

    except OrderAlreadyCancelledError as error:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"Order is already cancelled: {error}",
        ) from error


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=HTTP_201_CREATED,
)
def register_user(user: UserCreate, db: DatabaseSession):
    created_user = create_user_in_db(db, user.username, user.password)

    if created_user is None:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    return created_user


@app.post("/auth/token", response_model=TokenResponse)
def login(form_data: LoginForm, db: DatabaseSession):
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )
    if user is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.username)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/auth/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser):
    return current_user
