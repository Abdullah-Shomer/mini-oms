from products import (
    add_product,
    delete_product,
    find_product_by_sku,
    update_product_quantity,
)


def show_menu():
    print("1. Add product")
    print("2. List products")
    print("3. Find product")
    print("4. Update quantity")
    print("5. Delete product")
    print("0. Exit")


def main():

    products = []

    while True:
        show_menu()

        choice = input("choice a number: ")

        if choice == "0":
            print("Goodbye!")
            break

        elif choice == "1":
            name = input("name: ")
            sku = input("sku: ")

            try:
                price = float(input("price: "))
                quantity = int(input("quantity: "))

            except ValueError:
                print("Price and quantity must be numbers.")

                continue

            result = add_product(products, name, sku, price, quantity)

            if result is True:
                print("Product added successfully.")

            else:
                print("Could not add product.")

        elif choice == "2":
            if not products:
                print("No products found.")

            else:
                for product in products:
                    print(product)

        elif choice == "3":
            target_sku = input("sku: ")

            found_product = find_product_by_sku(products, target_sku)

            if found_product is None:
                print("Product not found.")
            else:
                print(found_product)

        elif choice == "4":
            target_sku = input("sku: ")

            try:
                new_quantity = int(input("new quantity: "))
            except ValueError:
                print("Quantity must be a whole number.")
                continue

            result = update_product_quantity(products, target_sku, new_quantity)

            if result is True:
                print("Quantity updated successfully.")

            else:
                print("Could not update quantity.")

        elif choice == "5":
            target_sku = input("sku: ")

            result = delete_product(products, target_sku)

            if result is True:
                print("Product deleted successfully.")

            else:
                print("Could not delete product.")

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
