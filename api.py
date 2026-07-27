from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from database import get_db
from product_repository import create_product as create_product_in_db
from product_repository import delete_product as delete_product_from_db
from product_repository import find_product_by_sku as find_product_by_sku_in_db
from product_repository import list_products as list_products_from_db
from product_repository import update_product_quantity as update_quantity_in_db

DatabaseSession = Annotated[Session, Depends(get_db)]


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


app = FastAPI()


@app.get("/")
def root():
    message = {"message": "Mini OMS API"}

    return message


@app.get("/products", response_model=list[ProductResponse])
def list_products(db: DatabaseSession):
    return list_products_from_db(db)


@app.post(
    "/products",
    status_code=HTTP_201_CREATED,
    response_model=ProductResponse,
)
def create_new_product(
    product: ProductCreate,
    db: DatabaseSession,
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
def update_quantity(sku: str, db: DatabaseSession, update: QuantityUpdate):
    result = update_quantity_in_db(db, sku, update.quantity)

    if result is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found")
    return result


@app.delete("/products/{sku}")
def remove_product(sku: str, db: DatabaseSession):

    result = delete_product_from_db(db, sku)

    if result is False:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found")

    return {"message": "Product deleted successfully"}
