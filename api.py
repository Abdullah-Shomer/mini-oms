from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from products import (
    add_product,
    delete_product,
    find_product_by_sku,
    update_product_quantity,
)


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    price: float = Field(ge=0)
    quantity: int = Field(ge=0)

    @field_validator("name", "sku")
    @classmethod
    def validate_text_fields(cls, value: str):
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Name and SKU must not be blank")
        return cleaned_value


class QuantityUpdate(BaseModel):
    quantity: int = Field(ge=0)


app = FastAPI()
products = []


@app.get("/")
def root():
    message = {"message": "Mini OMS API"}

    return message


@app.get("/products")
def list_products():

    return products


@app.post("/products", status_code=HTTP_201_CREATED)
def create_new_product(product: ProductCreate):

    result = add_product(
        products, product.name, product.sku, product.price, product.quantity
    )

    if result is False:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Could not add product"
        )

    return product


@app.get("/products/{sku}")
def get_product(sku: str):
    found_product = find_product_by_sku(products, sku)
    if found_product is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found")

    return found_product


@app.patch("/products/{sku}/quantity")
def update_quantity(sku: str, update: QuantityUpdate):
    result = update_product_quantity(products, sku, update.quantity)

    if result is False:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Could not update quantity"
        )

    updated_product = find_product_by_sku(products, sku)
    return updated_product


@app.delete("/products/{sku}")
def remove_product(sku: str):

    result = delete_product(products, sku)

    if result is False:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found")

    return {"message": "Product deleted successfully"}
