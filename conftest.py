import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

from api import app
from database import database_url, get_db
from models import Order, Product, User
from security import create_access_token
from user_repository import create_user

test_database_url = database_url.set(database="mini_oms_test")

if test_database_url.database != "mini_oms_test":
    raise RuntimeError("Tests must use the test database")

test_engine = create_engine(test_database_url)
TestSessionLocal = sessionmaker(bind=test_engine)


def override_get_db():
    with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_database():
    with TestSessionLocal() as session:
        session.execute(delete(Order))
        session.execute(delete(Product))
        session.execute(delete(User))
        session.commit()

    yield

    with TestSessionLocal() as session:
        session.execute(delete(Order))
        session.execute(delete(Product))
        session.execute(delete(User))
        session.commit()


@pytest.fixture
def db_session():
    with TestSessionLocal() as session:
        yield session


@pytest.fixture
def admin_headers(db_session):
    user = create_user(
        db_session,
        "admin",
        "secret123",
    )

    assert user is not None

    user.role = "admin"
    db_session.commit()

    access_token = create_access_token(user.username)

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def operator_headers(db_session):
    user = create_user(
        db_session,
        "operator",
        "secret123",
    )

    assert user is not None

    access_token = create_access_token(user.username)

    return {"Authorization": f"Bearer {access_token}"}
