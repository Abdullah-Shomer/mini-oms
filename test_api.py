from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_CONTENT
from api import app , products


client = TestClient(app)



def test_root():
    response = client.get("/")

    assert response.status_code == HTTP_200_OK
    assert response.json() == {"message": "Mini OMS API"}




def test_create_product():
    products.clear()
    response = client.post("/products", json={
            "name":"Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10
        })
    assert response.status_code == HTTP_201_CREATED
    assert response.json()["sku"] == "KB-001"
    assert len(products) == 1 



def test_create_duplicate_product():
    products.clear()
    first_response = client.post("/products", json={
            "name":"Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10
            })
    duplicate_response = client.post("/products", json={
            "name":"Another Keyboard",
            "sku": "KB-001",
            "price": 30,
            "quantity": 5
            })
    
    assert duplicate_response.status_code == HTTP_400_BAD_REQUEST
    assert len(products) == 1 



def test_get_existing_product():
    products.clear()
    client.post("/products", json={
            "name":"Keyboard",
            "sku": "KB-001",
            "price": 25,
            "quantity": 10
            })
    
    response = client.get("/products/KB-001")

    assert response.status_code == HTTP_200_OK
    assert response.json()["sku"] == "KB-001"




def test_get_missing_product():
    products.clear()
    response = client.get("/products/XX-999")

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found"



def test_update_product_quantity():
    products.clear()
    client.post("/products", json={
                "name":"Keyboard",
                "sku": "KB-001",
                "price": 25,
                "quantity": 10
                })

    
    response = client.patch("/products/KB-001/quantity", json={
                "quantity": 20
                })
    assert response.status_code == HTTP_200_OK
    assert response.json()["quantity"] == 20
    


def test_update_negative_quantity():
    products.clear()
    client.post("/products", json={
                    "name":"Keyboard",
                    "sku": "KB-001",
                    "price": 25,
                    "quantity": 10
                    })

    
    response = client.patch("/products/KB-001/quantity", json={
                    "quantity": -5
                    })
    product_response = client.get("/products/KB-001")


    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    assert product_response.json()["quantity"] == 10



def test_delete_product():
    products.clear()
    client.post("/products", json={
                    "name":"Keyboard",
                    "sku": "KB-001",
                    "price": 25,
                    "quantity": 10
                    })
    
    response = client.delete("/products/KB-001")


    assert response.status_code == HTTP_200_OK
    assert response.json()["message"] == "Product deleted successfully"
    assert len(products) == 0



def test_delete_missing_product():
    products.clear()

    response = client.delete("/products/XX-999")

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Product not found"
    assert len(products) == 0
    

def test_list_products():
    products.clear()

    client.post("/products", json={
                        "name":"Keyboard",
                        "sku": "KB-001",
                        "price": 25,
                        "quantity": 10
                        })
    
    client.post("/products", json={
                        "name":"Keyboard",
                        "sku": "KB-002",
                        "price": 25,
                        "quantity": 10
                        })

    
    response = client.get("/products")

    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 2