import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

from api import app
from database import database_url, get_db
from models import Order, Product

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
        session.commit()

    yield

    with TestSessionLocal() as session:
        session.execute(delete(Order))
        session.execute(delete(Product))
        session.commit()
