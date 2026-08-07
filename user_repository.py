from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import User
from security import hash_password, verify_password


def find_user_by_username(
    session: Session,
    username: str,
) -> User | None:
    statement = select(User).where(User.username == username)

    return session.scalar(statement)


def create_user(
    session: Session,
    username: str,
    password: str,
) -> User | None:

    hashed_password = hash_password(password)

    user = User(
        username=username,
        hashed_password=hashed_password,
    )
    try:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    except IntegrityError:
        session.rollback()
        return None


def authenticate_user(
    session: Session,
    username: str,
    password: str,
) -> User | None:

    user = find_user_by_username(session, username)

    if user is None:
        return None

    password_is_valid = verify_password(
        password,
        user.hashed_password,
    )

    if password_is_valid is False:
        return None

    return user
