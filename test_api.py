from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_CONTENT,
)

from api import app
from security import create_access_token
from user_repository import create_user

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == HTTP_200_OK
    assert response.json() == {"message": "Mini OMS API"}


def test_create_product(admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )
    assert response.status_code == HTTP_201_CREATED
    assert response.json()["sku"] == "KB-001"
    list_response = client.get("/products")
    assert len(list_response.json()) == 1


def test_create_duplicate_product(admin_headers):

    client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )
    duplicate_response = client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Another Keyboard", "sku": "KB-001", "price": 30, "quantity": 5},
    )

    assert duplicate_response.status_code == HTTP_409_CONFLICT
    assert len(client.get("/products").json()) == 1


def test_get_existing_product(admin_headers):

    client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    response = client.get("/products/KB-001")

    assert response.status_code == HTTP_200_OK
    assert response.json()["sku"] == "KB-001"


def test_get_missing_product():

    response = client.get("/products/XX-999")

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found"


def test_update_product_quantity(admin_headers):

    client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    response = client.patch(
        "/products/KB-001/quantity", headers=admin_headers, json={"quantity": 20}
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["quantity"] == 20


def test_update_negative_quantity(admin_headers):

    client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    response = client.patch(
        "/products/KB-001/quantity", headers=admin_headers, json={"quantity": -5}
    )
    product_response = client.get("/products/KB-001")

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert product_response.json()["quantity"] == 10


def test_delete_product(admin_headers):

    client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    response = client.delete("/products/KB-001", headers=admin_headers)

    assert response.status_code == HTTP_200_OK
    assert response.json()["message"] == "Product deleted successfully"
    assert client.get("/products").json() == []


def test_delete_missing_product(admin_headers):

    response = client.delete("/products/XX-999", headers=admin_headers)

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found"
    assert client.get("/products").json() == []


def test_list_products(admin_headers):

    client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "KB-002", "price": 25, "quantity": 10},
    )

    response = client.get("/products")

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 2


def test_create_product_empty_name(admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json={"name": "", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert client.get("/products").json() == []


def test_create_product_empty_sku(admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "", "price": 25, "quantity": 10},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert client.get("/products").json() == []


def test_create_product_blank_name(admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json={"name": "   ", "sku": "KB-001", "price": 25, "quantity": 10},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert client.get("/products").json() == []


def test_create_product_blank_sku(admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json={"name": "Keyboard", "sku": "   ", "price": 25, "quantity": 10},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert client.get("/products").json() == []


def test_create_product_strips_whitespace(admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json={"name": "  Keyboard  ", "sku": "  KB-001  ", "price": 25, "quantity": 10},
    )

    assert response.status_code == HTTP_201_CREATED
    assert response.json()["name"] == "Keyboard"
    assert response.json()["sku"] == "KB-001"
    assert len(client.get("/products").json()) == 1


def test_create_order_success(admin_headers):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    response = client.post(
        "/orders",
        headers=admin_headers,
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


def test_create_order_rolls_back_when_product_is_missing(admin_headers):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )

    response = client.post(
        "/orders",
        headers=admin_headers,
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


def test_create_order_rejects_insufficient_stock(admin_headers):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    response = client.post(
        "/orders",
        headers=admin_headers,
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


def test_create_order_rejects_duplicate_skus(operator_headers):
    response = client.post(
        "/orders",
        headers=operator_headers,
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


def test_create_order_rejects_empty_items(operator_headers):
    response = client.post(
        "/orders",
        headers=operator_headers,
        json={"items": []},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


def test_create_order_rejects_zero_quantity(operator_headers):
    response = client.post(
        "/orders",
        headers=operator_headers,
        json={"items": [{"sku": "KB-001", "quantity": 0}]},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


def test_create_order_rejects_blank_sku(operator_headers):
    response = client.post(
        "/orders",
        headers=operator_headers,
        json={"items": [{"sku": "     ", "quantity": 1}]},
    )

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert "SKU must not be blank" in response.json()["detail"][0]["msg"]


def test_list_orders(admin_headers):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    client.post(
        "/orders",
        headers=admin_headers,
        json={
            "items": [
                {
                    "sku": "KB-001",
                    "quantity": 2,
                }
            ]
        },
    )

    response = client.get("/orders", headers=admin_headers)

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "pending"
    assert response.json()[0]["items"][0]["quantity"] == 2


def test_get_existing_order(admin_headers):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    create_response = client.post(
        "/orders",
        headers=admin_headers,
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
    response = client.get(f"/orders/{order_id}", headers=admin_headers)

    assert response.status_code == HTTP_200_OK
    assert response.json()["id"] == order_id
    assert response.json()["items"][0]["quantity"] == 2


def test_get_missing_order():
    response = client.get("/orders/999999")

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Order not found"


def test_cancel_order_restores_stock(admin_headers):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    create_response = client.post(
        "/orders",
        headers=admin_headers,
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
    response = client.post(f"/orders/{order_id}/cancel", headers=admin_headers)
    product_response = client.get("/products/KB-001")

    assert response.status_code == HTTP_200_OK
    assert response.json()["status"] == "cancelled"
    assert product_response.json()["quantity"] == 10


def test_cancel_order_twice_does_not_restore_stock_twice(
    admin_headers,
):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    create_response = client.post(
        "/orders",
        headers=admin_headers,
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

    first_response = client.post(f"/orders/{order_id}/cancel", headers=admin_headers)
    second_response = client.post(f"/orders/{order_id}/cancel", headers=admin_headers)

    product_response = client.get("/products/KB-001")

    assert first_response.status_code == HTTP_200_OK
    assert first_response.json()["status"] == "cancelled"

    assert second_response.status_code == HTTP_409_CONFLICT
    assert second_response.json()["detail"] == (
        f"Order is already cancelled: {order_id}"
    )

    assert product_response.json()["quantity"] == 10


def test_cancel_missing_order(operator_headers):
    response = client.post("/orders/999999/cancel", headers=operator_headers)

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Order not found: 999999"


def test_register_user():
    response = client.post(
        "/auth/register",
        json={"username": "abdallah", "password": "secret123"},
    )

    assert response.status_code == HTTP_201_CREATED
    assert response.json()["username"] == "abdallah"
    assert response.json()["role"] == "operator"
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()


def test_register_user_rejects_duplicate_username():
    first_response = client.post(
        "/auth/register",
        json={"username": "abdallah", "password": "secret123"},
    )

    second_response = client.post(
        "/auth/register",
        json={"username": "abdallah", "password": "secret123"},
    )

    assert first_response.status_code == HTTP_201_CREATED
    assert second_response.status_code == HTTP_409_CONFLICT
    assert second_response.json()["detail"] == "Username already exists"


def test_login_success():
    response = client.post(
        "/auth/register",
        json={"username": "abdallah", "password": "secret123"},
    )

    user_login = client.post(
        "/auth/token",
        data={
            "username": "abdallah",
            "password": "secret123",
        },
    )

    assert response.status_code == HTTP_201_CREATED
    assert user_login.status_code == HTTP_200_OK
    assert user_login.json()["token_type"] == "bearer"
    access_token = user_login.json()["access_token"]
    assert isinstance(access_token, str)
    assert access_token


def test_login_rejects_wrong_password():
    response = client.post(
        "/auth/register",
        json={"username": "abdallah", "password": "secret123"},
    )

    user_login = client.post(
        "/auth/token",
        data={
            "username": "abdallah",
            "password": "wrong-password",
        },
    )

    assert response.status_code == HTTP_201_CREATED
    assert user_login.status_code == HTTP_401_UNAUTHORIZED
    assert user_login.json()["detail"] == "Incorrect username or password"
    assert user_login.headers["www-authenticate"] == "Bearer"


def test_get_current_user():
    response = client.post(
        "/auth/register",
        json={"username": "abdallah", "password": "secret123"},
    )
    user_login = client.post(
        "/auth/token",
        data={
            "username": "abdallah",
            "password": "secret123",
        },
    )
    access_token = user_login.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTP_201_CREATED
    assert user_login.status_code == HTTP_200_OK
    assert me_response.status_code == HTTP_200_OK
    assert me_response.json()["username"] == "abdallah"
    assert me_response.json()["role"] == "operator"
    assert "password" not in me_response.json()
    assert "hashed_password" not in me_response.json()


def test_get_current_user_requires_token():
    response = client.get("/auth/me")

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_current_user_rejects_invalid_token():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate credentials"
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_current_user_rejects_inactive_user(db_session):
    user = create_user(
        db_session,
        "abdallah",
        "secret123",
    )

    assert user is not None

    user.is_active = False
    db_session.commit()

    access_token = create_access_token(user.username)

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate credentials"
    assert response.headers["www-authenticate"] == "Bearer"


def test_create_product_requires_authentication():
    response = client.post(
        "/products",
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_create_product_rejects_operator():
    client.post(
        "/auth/register",
        json={
            "username": "operator",
            "password": "secret123",
        },
    )

    login_response = client.post(
        "/auth/token",
        data={
            "username": "operator",
            "password": "secret123",
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/products",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )
    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Admin access required"


def test_list_products_pagination(admin_headers):
    for i in range(1, 4):
        client.post(
            "/products",
            headers=admin_headers,
            json={
                "name": f"Product {i}",
                "sku": f"KB-{i:03d}",
                "price": 10 + i,
                "quantity": 5 + i,
            },
        )

    response = client.get("/products?skip=1&limit=1")

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == "KB-002"


def test_list_products_rejects_negative_skip():
    response = client.get("/products?skip=-1&limit=20")

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


def test_list_products_rejects_limit_above_maximum():
    response = client.get("/products?skip=0&limit=101")

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT


def test_list_products_filters_by_name(admin_headers):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )

    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Mouse",
            "sku": "MS-001",
            "price": 15,
            "quantity": 20,
        },
    )

    response = client.get("/products?search=key")

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Keyboard"


def test_list_products_filters_by_sku(admin_headers):
    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10,
        },
    )

    client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Mouse",
            "sku": "MS-001",
            "price": 15,
            "quantity": 20,
        },
    )

    response = client.get("/products?search=ms-001")

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == "MS-001"
