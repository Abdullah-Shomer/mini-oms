from user_repository import (
    authenticate_user,
    create_user,
    find_user_by_username,
)


def test_create_user_success(db_session):
    user = create_user(
        db_session,
        "abdallah",
        "secret123",
    )
    assert user is not None
    assert user.username == "abdallah"
    assert user.hashed_password != "secret123"


def test_create_user_rejects_duplicate_username(db_session):
    first_user = create_user(
        db_session,
        "abdallah",
        "secret123",
    )

    second_user = create_user(
        db_session,
        "abdallah",
        "secret123",
    )

    assert first_user is not None
    assert second_user is None


def test_authenticate_user_success(db_session):
    user = create_user(
        db_session,
        "abdallah",
        "secret123",
    )
    authenticated_user = authenticate_user(
        db_session,
        "abdallah",
        "secret123",
    )

    assert user is not None
    assert authenticated_user is not None
    assert authenticated_user.username == "abdallah"


def test_find_user_by_username(db_session):
    user = create_user(
        db_session,
        "abdallah",
        "secret123",
    )
    found_user = find_user_by_username(db_session, "abdallah")

    assert user is not None
    assert found_user is not None
    assert found_user.username == "abdallah"


def test_authenticate_user_rejects_wrong_password(db_session):
    user = create_user(
        db_session,
        "abdallah",
        "secret123",
    )
    authenticated_user = authenticate_user(
        db_session,
        "abdallah",
        "wrongpassword",
    )

    assert user is not None
    assert authenticated_user is None


def test_authenticate_user_rejects_missing_user(db_session):
    authenticated_user = authenticate_user(
        db_session,
        "missing",
        "secret123",
    )
    assert authenticated_user is None
