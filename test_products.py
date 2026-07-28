from products import (
    add_product,
    delete_product,
    find_product_by_sku,
    update_product_quantity,
)


def test_add_product_success():
    products = []

    result = add_product(products, "Keyboard", "KB-001", 25, 10)
    assert result is True
    assert len(products) == 1


def test_add_product_duplicate_sku():
    products = []

    duplicate_result = add_product(products, "Keyboard", "KB-001", 25, 10)
    assert duplicate_result is True
    assert len(products) == 1

    second_result = add_product(products, "Another Keyboard", "KB-001", 25, 10)
    assert second_result is False
    assert len(products) == 1


def test_add_product_negative_price():
    products = []

    result = add_product(products, "Keyboard", "KB-001", -25, 10)
    assert result is False
    assert len(products) == 0


def test_find_existing_product():
    products = []
    result = add_product(products, "Keyboard", "KB-001", 25, 10)

    found_product = find_product_by_sku(products, "KB-001")

    assert result is True
    assert found_product is not None
    assert found_product["name"] == "Keyboard"
    assert found_product["sku"] == "KB-001"


def test_find_missing_product():
    products = []

    result = find_product_by_sku(products, "XX-999")
    assert result is None


def test_update_product_quantity_success():
    products = []

    result = add_product(products, "Keyboard", "KB-001", 25, 10)

    update_result = update_product_quantity(products, "KB-001", 20)

    found_product = find_product_by_sku(products, "KB-001")

    assert result is True
    assert update_result is True
    assert found_product["quantity"] == 20


def test_update_missing_product():
    products = []

    result = update_product_quantity(products, "XX-999", 20)
    assert result is False
    assert len(products) == 0


def test_update_product_negative_quantity():
    products = []

    result = add_product(products, "Keyboard", "KB-001", 20, 10)

    updated_result = update_product_quantity(products, "KB-001", -5)

    found_product = find_product_by_sku(products, "KB-001")

    assert result is True
    assert updated_result is False
    assert found_product is not None
    assert found_product["quantity"] == 10


def test_delete_existing_product():
    products = []

    result = add_product(products, "Keyboard", "KB-001", 20, 10)

    delete_result = delete_product(products, "KB-001")

    found_product = find_product_by_sku(products, "KB-001")

    assert result is True
    assert delete_result is True
    assert found_product is None
    assert len(products) == 0


def test_delete_missing_product():
    products = []

    result = delete_product(products, "XX-999")

    assert result is False
    assert len(products) == 0
