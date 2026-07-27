from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Product


def create_product(
    session: Session,
    name: str,
    sku: str,
    price: Decimal,
    quantity: int,
) -> Product | None:
    product = Product(
        name=name,
        sku=sku,
        price=price,
        quantity=quantity,
    )

    session.add(product)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return None

    session.refresh(product)

    return product


def find_product_by_sku(
    session: Session,
    sku: str,
) -> Product | None:
    statement = select(Product).where(Product.sku == sku)

    return session.scalar(statement)


def list_products(session: Session) -> list[Product]:
    statement = select(Product).order_by(Product.id)

    return list(session.scalars(statement).all())


def update_product_quantity(
    session: Session,
    sku: str,
    quantity: int,
) -> Product | None:

    product = find_product_by_sku(session, sku)

    if product is None:
        return None

    product.quantity = quantity
    session.commit()
    session.refresh(product)
    return product


def delete_product(
    session: Session,
    sku: str,
) -> bool:

    product = find_product_by_sku(session, sku)

    if product is None:
        return False

    session.delete(product)
    session.commit()
    return True
