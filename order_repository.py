from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Order, OrderItem, Product


class ProductNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


def create_order(
    session: Session,
    items: list[tuple[str, int]],
) -> Order:
    try:
        order = Order()
        session.add(order)
        for sku, quantity in items:
            statement = select(Product).where(Product.sku == sku).with_for_update()

            product = session.scalar(statement)
            if product is None:
                raise ProductNotFoundError(sku)

            if quantity > product.quantity:
                raise InsufficientStockError(sku)

            product.quantity -= quantity

            order_item = OrderItem(
                product=product,
                quantity=quantity,
                unit_price=product.price,
            )

            order.items.append(order_item)

        session.commit()
        session.refresh(order)
        return order

    except Exception:
        session.rollback()
        raise


def list_orders(session: Session) -> list[Order]:
    statement = select(Order).options(selectinload(Order.items)).order_by(Order.id)

    return list(session.scalars(statement).all())


def find_order_by_id(
    session: Session,
    order_id: int,
) -> Order | None:
    statement = (
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )

    return session.scalar(statement)


class OrderNotFoundError(Exception):
    pass


class OrderAlreadyCancelledError(Exception):
    pass


def cancel_order(
    session: Session,
    order_id: int,
) -> Order:
    try:
        statement = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
            .with_for_update()
        )

        order = session.scalar(statement)

        if order is None:
            raise OrderNotFoundError(order_id)

        if order.status == "cancelled":
            raise OrderAlreadyCancelledError(order_id)

        for item in order.items:
            product_statement = (
                select(Product).where(Product.id == item.product_id).with_for_update()
            )

            product = session.scalar(product_statement)
            product.quantity += item.quantity

        order.status = "cancelled"

        session.commit()
        session.refresh(order)

        return order

    except Exception:
        session.rollback()
        raise
