from datetime import datetime, timedelta, timezone

import jwt

from config import settings
from security import create_access_token, decode_access_token


def test_access_token_round_trip():
    token = create_access_token("abdallah")
    decoded_token = decode_access_token(token)

    assert isinstance(token, str)
    assert decoded_token == "abdallah"


def test_decode_access_token_rejects_invalid_token():
    decoded_token = decode_access_token("not-a-valid-token")

    assert decoded_token is None


def test_decode_access_token_rejects_expired_token():
    payload = {
        "sub": "abdallah",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    decoded_token = decode_access_token(token)

    assert decoded_token is None
