def find_product_by_sku(products, target_sku):

    for product in products:

        if product["sku"] ==  target_sku:
            return product

    return None




def update_product_quantity(products, target_sku, quantity):

    if quantity < 0:
        return False
    
    found_product = find_product_by_sku(
    products,
    target_sku,
    )
    if found_product is None:
        return False

    found_product["quantity"] = quantity
    
    return True



def create_product(name, sku, price, quantity):

    product = {
    "name": name,
    "sku": sku,
    "price": price,
    "quantity": quantity,
}
    return product 



def add_product(products, name, sku, price, quantity):

    if price  <0 or quantity < 0:
        return False

    existing_product = find_product_by_sku(
    products,
    sku,
    )
    if existing_product is not None:
        return False

    new_product = create_product(
    name,
    sku,
    price,
    quantity,
)

    products.append(new_product)
    return True 




def delete_product(products, sku):
        
    deleted_product = find_product_by_sku(
    products,
    sku,
    )
    if deleted_product is None:
        return False
    
    products.remove(deleted_product)
    return True 
