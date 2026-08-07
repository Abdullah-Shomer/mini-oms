from collections.abc import Generator

from sqlalchemy import URL, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings

if settings.database_url:
    database_url = make_url(settings.database_url)

    if database_url.drivername == "postgresql":
        database_url = database_url.set(drivername="postgresql+psycopg")
else:
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )

engine = create_engine(database_url)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
