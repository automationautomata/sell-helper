from datetime import datetime, timedelta, timezone

import jwt
import pytest
from app.core.infrastructure.auth import (
    InvalidPayloadTypeError,
    InvalidTokenError,
    JWTAuth,
    JWTToken,
)
from app.data import EnvKeys
from pydantic import BaseModel


class UserPayload(BaseModel):
    username: str
    role: str


@pytest.fixture(autouse=True)
def mock_env_secret(monkeypatch):
    """Automatically set JWT secret for all tests."""
    monkeypatch.setenv(EnvKeys.JWT_SECRET, "secretkey")


@pytest.fixture
def jwt_auth():
    return JWTAuth(jwt_ttl_minutes=15, jwt_algorithm="HS256")


def test_generate_token_creates_valid_token(monkeypatch, jwt_auth):
    def mock_encode(payload, secret, algorithm):
        return "fakejwttoken"

    monkeypatch.setattr(jwt, "encode", mock_encode)

    data = UserPayload(username="alice", role="admin")

    token_obj = jwt_auth.generate_token(data)

    assert isinstance(token_obj, JWTToken)
    assert token_obj.token == "fakejwttoken"
    assert token_obj.expires_at > datetime.now(timezone.utc)
    assert token_obj.expires_at - datetime.now(timezone.utc) <= timedelta(minutes=15)


def test_generate_token_encodes_correct_payload(monkeypatch, jwt_auth):
    captured_payload = {}

    def mock_encode(payload, secret, algorithm):
        captured_payload.update(payload)
        return "token"

    monkeypatch.setattr(jwt, "encode", mock_encode)
    data = UserPayload(username="bob", role="user")

    token = jwt_auth.generate_token(data)

    assert "exp" in captured_payload
    assert captured_payload["data"]["username"] == "bob"
    assert captured_payload["data"]["role"] == "user"
    assert token.token == "token"


def test_verify_token_success(monkeypatch, jwt_auth):
    def mock_decode(token, secret=None, algorithms=None):
        return {"data": {"username": "carol", "role": "admin"}}

    monkeypatch.setattr(jwt, "decode", mock_decode)

    result = jwt_auth.verify_token("validtoken", UserPayload)

    assert isinstance(result, UserPayload)
    assert result.username == "carol"
    assert result.role == "admin"


def test_verify_token_invalid_token(monkeypatch, jwt_auth):
    def mock_decode(token, secret=None, algorithms=None):
        raise jwt.InvalidTokenError("bad token")

    monkeypatch.setattr(jwt, "decode", mock_decode)

    with pytest.raises(InvalidTokenError):
        jwt_auth.verify_token("badtoken", UserPayload)


def test_verify_token_expired_signature(monkeypatch, jwt_auth):
    def mock_decode(token, secret=None, algorithms=None):
        raise jwt.ExpiredSignatureError("expired")

    monkeypatch.setattr(jwt, "decode", mock_decode)

    with pytest.raises(InvalidTokenError):
        jwt_auth.verify_token("expiredtoken", UserPayload)


def test_verify_token_invalid_payload_type(monkeypatch, jwt_auth):
    def mock_decode(token, secret=None, algorithms=None):
        return {"data": {"username": 123, "role": "user"}}

    monkeypatch.setattr(jwt, "decode", mock_decode)

    with pytest.raises(InvalidPayloadTypeError):
        jwt_auth.verify_token("invalidpayload", UserPayload)
