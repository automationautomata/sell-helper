from datetime import datetime, timedelta, timezone

import pytest
from app.core.domain.user import User
from app.core.infrastructure.auth import InvalidTokenError, JWTToken
from app.core.services.auth import AuthService, Token


@pytest.fixture
def mock_hasher(mocker):
    hasher = mocker.Mock()
    hasher.verify.return_value = True
    return hasher


@pytest.fixture
def mock_user_repo(mocker):
    repo = mocker.AsyncMock()
    return repo


@pytest.fixture
def mock_jwt_auth(mocker):
    jwt = mocker.Mock()
    return jwt


@pytest.fixture
def auth_service(mock_hasher, mock_user_repo, mock_jwt_auth):
    return AuthService(
        hasher=mock_hasher, user_repo=mock_user_repo, jwt_auth=mock_jwt_auth
    )


@pytest.mark.asyncio
async def test_verify_user_success(auth_service, mock_user_repo, mock_hasher):
    user = User(email="abc@mail.rnd", password_hash="hash")
    mock_user_repo.get_user_by_email.return_value = user
    mock_hasher.verify.return_value = True

    result = await auth_service.verify_user("abc@mail.rnd", "password123")

    mock_user_repo.get_user_by_email.assert_awaited_once_with("abc@mail.rnd")
    mock_hasher.verify.assert_called_once_with("password123", "hash")
    assert result is True


@pytest.mark.asyncio
async def test_verify_user_incorrect_password(
    auth_service, mock_user_repo, mock_hasher
):
    user = User(email="abc@mail.rnd", password_hash="hash")
    mock_user_repo.get_user_by_email.return_value = user
    mock_hasher.verify.return_value = False

    result = await auth_service.verify_user("abc@mail.rnd", "wrongpass")

    assert result is False


@pytest.mark.asyncio
async def test_verify_user_not_found(auth_service, mock_user_repo):
    mock_user_repo.get_user_by_email.return_value = None

    result = await auth_service.verify_user("abc@mail.rnd", "password")

    assert result is False


def test_create_access_token_returns_token(auth_service, mock_jwt_auth):
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    jwt_token = JWTToken(token="123456", expires_at=expires)
    mock_jwt_auth.generate_token.return_value = jwt_token

    token = auth_service.create_access_token("abc@mail.rnd")

    mock_jwt_auth.generate_token.assert_called_once()
    assert isinstance(token, Token)
    assert token.token == "123456"
    assert token.ttl_seconds == int(expires.timestamp())


@pytest.mark.asyncio
async def test_validate_valid_token(auth_service, mock_jwt_auth, mock_user_repo):
    payload = AuthService.TokenPayload(email="abc@mail.rnd")
    mock_jwt_auth.verify_token.return_value = payload
    user = User(email="abc@mail.rnd", password_hash="hash")
    mock_user_repo.get_user_by_email.return_value = user

    result = await auth_service.validate("validtoken")

    mock_jwt_auth.verify_token.assert_called_once_with(
        "validtoken", AuthService.TokenPayload
    )
    mock_user_repo.get_user_by_email.assert_awaited_once_with("abc@mail.rnd")
    assert result == user


@pytest.mark.asyncio
async def test_validate_invalid_token_returns_none(auth_service, mock_jwt_auth):
    mock_jwt_auth.verify_token.side_effect = InvalidTokenError()

    result = await auth_service.validate("invalidtoken")

    assert result is None


@pytest.mark.asyncio
async def test_validate_user_not_found_returns_none(
    auth_service, mock_jwt_auth, mock_user_repo
):
    payload = AuthService.TokenPayload(email="abc@mail.rnd")
    mock_jwt_auth.verify_token.return_value = payload
    mock_user_repo.get_user_by_email.return_value = None

    result = await auth_service.validate("token")

    assert result is None
