from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_CONTENT,
)

from api import app

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == HTTP_200_OK
    assert response.json() == {"message": "Mini OMS API"}


def test_create_product():

    response = client.post(
        "/products",
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )
    assert response.status_code == HTTP_201_CREATED
    assert response.json()["sku"] == "KB-001"
    list_response = client.get("/products")
    assert len(list_response.json()) == 1


def test_create_duplicate_product():

    client.post(
        "/products",
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )
    duplicate_response = client.post(
        "/products",
        json={"name": "Another Keyboard", "sku": "KB-001", "price": 30, "quantity": 5},
    )

    assert duplicate_response.status_code == HTTP_409_CONFLICT
    assert len(client.get("/products").json()) == 1


def test_get_existing_product():

    client.post(
        "/products",
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    response = client.get("/products/KB-001")

    assert response.status_code == HTTP_200_OK
    assert response.json()["sku"] == "KB-001"


def test_get_missing_product():

    response = client.get("/products/XX-999")

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found"


def test_update_product_quantity():

    client.post(
        "/products",
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    response = client.patch("/products/KB-001/quantity", json={"quantity": 20})
    assert response.status_code == HTTP_200_OK
    assert response.json()["quantity"] == 20


def test_update_negative_quantity():

    client.post(
        "/products",
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    response = client.patch("/products/KB-001/quantity", json={"quantity": -5})
    product_response = client.get("/products/KB-001")

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert product_response.json()["quantity"] == 10


def test_delete_product():

    client.post(
        "/products",
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    response = client.delete("/products/KB-001")

    assert response.status_code == HTTP_200_OK
    assert response.json()["message"] == "Product deleted successfully"
    assert client.get("/products").json() == []


def test_delete_missing_product():

    response = client.delete("/products/XX-999")

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found"
    assert client.get("/products").json() == []


def test_list_products():

    client.post(
        "/products",
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    client.post(
        "/products",
        json={"name": "Keyboard", "sku": "KB-002", "price": 25, "quantity": 10},
    )

    response = client.get("/products")

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 2


def test_create_product_empty_name():

    response = client.post(
        "/products", json={"name": "", "sku": "KB-001", "price": 25, "quantity": 10}
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert client.get("/products").json() == []


def test_create_product_empty_sku():

    response = client.post(
        "/products", json={"name": "Keyboard", "sku": "", "price": 25, "quantity": 10}
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert client.get("/products").json() == []


def test_create_product_blank_name():

    response = client.post(
        "/products", json={"name": "   ", "sku": "KB-001", "price": 25, "quantity": 10}
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert client.get("/products").json() == []


def test_create_product_blank_sku():

    response = client.post(
        "/products",
        json={"name": "Keyboard", "sku": "   ", "price": 25, "quantity": 10},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert client.get("/products").json() == []


def test_create_product_strips_whitespace():

    response = client.post(
        "/products",
        json={"name": "  Keyboard  ", "sku": "  KB-001  ", "price": 25, "quantity": 10},
    )

    assert response.status_code == HTTP_201_CREATED
    assert response.json()["name"] == "Keyboard"
    assert response.json()["sku"] == "KB-001"
    assert len(client.get("/products").json()) == 1


def test_create_order_success():
    client.post(
        "/products",
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "sku": "KB-001",
                    "quantity": 2,
                }
            ]
        },
    )
    body = response.json()

    assert response.status_code == HTTP_201_CREATED
    assert body["status"] == "pending"
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 2
    assert body["items"][0]["unit_price"] == "25.00"

    product_response = client.get("/products/KB-001")

    assert product_response.json()["quantity"] == 8


def test_create_order_rolls_back_when_product_is_missing():
    client.post(
        "/products",
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )

    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "sku": "KB-001",
                    "quantity": 2,
                },
                {
                    "sku": "XX-999",
                    "quantity": 1,
                },
            ]
        },
    )

    product_response = client.get("/products/KB-001")

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found: XX-999"
    assert product_response.json()["quantity"] == 10


def test_create_order_rejects_insufficient_stock():
    client.post(
        "/products",
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "sku": "KB-001",
                    "quantity": 11,
                }
            ]
        },
    )

    product_response = client.get("/products/KB-001")

    assert response.status_code == HTTP_409_CONFLICT
    assert response.json()["detail"] == "Insufficient stock for SKU: KB-001"
    assert product_response.json()["quantity"] == 10


def test_create_order_rejects_duplicate_skus():
    response = client.post(
        "/orders",
        json={
            "items": [
                {"sku": "KB-001", "quantity": 1},
                {"sku": "KB-001", "quantity": 2},
            ]
        },
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert (
        "Each SKU may appear only once per order" in response.json()["detail"][0]["msg"]
    )


def test_create_order_rejects_empty_items():
    response = client.post(
        "/orders",
        json={"items": []},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


def test_create_order_rejects_zero_quantity():
    response = client.post(
        "/orders", json={"items": [{"sku": "KB-001", "quantity": 0}]}
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


def test_create_order_rejects_blank_sku():
    response = client.post("/orders", json={"items": [{"sku": "     ", "quantity": 1}]})

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert "SKU must not be blank" in response.json()["detail"][0]["msg"]


def test_list_orders():
    client.post(
        "/products",
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    client.post(
        "/orders",
        json={
            "items": [
                {
                    "sku": "KB-001",
                    "quantity": 2,
                }
            ]
        },
    )

    response = client.get("/orders")

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "pending"
    assert response.json()[0]["items"][0]["quantity"] == 2


def test_get_existing_order():
    client.post(
        "/products",
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    create_response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "sku": "KB-001",
                    "quantity": 2,
                }
            ]
        },
    )

    order_id = create_response.json()["id"]
    response = client.get(f"/orders/{order_id}")

    assert response.status_code == HTTP_200_OK
    assert response.json()["id"] == order_id
    assert response.json()["items"][0]["quantity"] == 2


def test_get_missing_order():
    response = client.get("/orders/999999")

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Order not found"
