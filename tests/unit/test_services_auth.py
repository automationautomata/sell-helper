from dataclasses import dataclass
import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, Mock

from app.services.auth import AuthService, TokenPayload
from app.domain.dto import Token
from app.domain.entities import User
from app.domain.ports import (
    AuthError,
    CannotCreateUser,
    InvalidUserToken,
)
from app.services.ports import (
    IHasher,
    IJWTAuth,
    IUserRepository,
    UserAlreadyExists,
    UserRepositoryError,
)


@dataclass
class MockJWTToken:
    token: str
    ttl: int


@pytest.fixture
def mock_hasher():
    hasher = Mock(spec=IHasher)
    hasher.hash.return_value = "hashed_password_value"
    hasher.verify.return_value = True
    return hasher


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock(spec=IUserRepository)
    return repo


@pytest.fixture
def mock_jwt_auth():
    jwt_auth = Mock(spec=IJWTAuth)
    jwt_auth.generate_token.return_value = MockJWTToken(
        token="jwt_token_value",
        ttl=250,
    )
    return jwt_auth


@pytest.fixture
def auth_service(mock_hasher, mock_user_repo, mock_jwt_auth):
    return AuthService(
        hasher=mock_hasher,
        user_repo=mock_user_repo,
        jwt_auth=mock_jwt_auth,
    )


@pytest.fixture
def test_user():
    user_uuid = uuid4()
    return User(
        uuid=user_uuid,
        email="test@example.com",
        password_hash="hashed_password_value",
    )


class TestAuthServiceVerifyUser:
    @pytest.mark.asyncio
    async def test_verify_user_success(
        self, auth_service, mock_user_repo, mock_hasher, test_user
    ):
        mock_user_repo.get_user_by_email.return_value = test_user
        mock_hasher.verify.return_value = True

        await auth_service.verify_user(test_user.email, "password123")

    @pytest.mark.asyncio
    async def test_verify_user_nonexistent_user(self, auth_service, mock_user_repo):
        mock_user_repo.get_user_by_email.return_value = None

        with pytest.raises(InvalidUserToken):
            await auth_service.verify_user("nonexistent@example.com", "password123")

    @pytest.mark.asyncio
    async def test_verify_user_wrong_password(
        self, auth_service, mock_user_repo, mock_hasher, test_user
    ):
        mock_user_repo.get_user_by_email.return_value = test_user
        mock_hasher.verify.return_value = False

        with pytest.raises(InvalidUserToken):
            await auth_service.verify_user("test@example.com", "wrong_password")

    @pytest.mark.asyncio
    async def test_verify_user_repository_error(self, auth_service, mock_user_repo):
        mock_user_repo.get_user_by_email.side_effect = UserRepositoryError(
            "Connection failed"
        )

        with pytest.raises(AuthError):
            await auth_service.verify_user("test@example.com", "password123")

    @pytest.mark.asyncio
    async def test_verify_user_email_password_mismatch(
        self, auth_service, mock_user_repo, mock_hasher, test_user
    ):
        mock_user_repo.get_user_by_email.return_value = test_user
        mock_hasher.verify.return_value = False

        with pytest.raises(InvalidUserToken):
            await auth_service.verify_user("test@example.com", "password123")


class TestAuthServiceAddUser:
    @pytest.mark.asyncio
    async def test_add_user_success(
        self, auth_service, mock_user_repo, mock_hasher, test_user
    ):
        mock_user_repo.add_user.return_value = test_user

        token = await auth_service.add_user("newuser@example.com", "password123")

        assert isinstance(token, Token)
        assert token.token == "jwt_token_value"
        mock_user_repo.add_user.assert_called_once_with(
            "newuser@example.com", "hashed_password_value"
        )
        mock_hasher.hash.assert_called_once_with("password123")

    @pytest.mark.asyncio
    async def test_add_user_already_exists(self, auth_service, mock_user_repo):
        mock_user_repo.add_user.side_effect = UserAlreadyExists("User exists")

        with pytest.raises(CannotCreateUser):
            await auth_service.add_user("existing@example.com", "password123")

    @pytest.mark.asyncio
    async def test_add_user_repository_error(self, auth_service, mock_user_repo):
        mock_user_repo.add_user.side_effect = UserRepositoryError("Connection failed")

        with pytest.raises(AuthError):
            await auth_service.add_user("test@example.com", "password123")

    @pytest.mark.asyncio
    async def test_add_user_hashes_password(
        self, auth_service, mock_user_repo, mock_hasher, test_user
    ):
        mock_user_repo.add_user.return_value = test_user

        await auth_service.add_user("test@example.com", "plaintext_password")

        mock_hasher.hash.assert_called_once_with("plaintext_password")


class TestAuthServiceValidate:
    @pytest.mark.asyncio
    async def test_validate_token_success(
        self, auth_service, mock_user_repo, mock_jwt_auth, test_user
    ):
        mock_jwt_auth.verify_token.return_value = TokenPayload(uuid=test_user.uuid)
        mock_user_repo.get_user_by_uuid.return_value = test_user

        result = await auth_service.validate("valid_token")

        assert result == test_user.uuid
        mock_jwt_auth.verify_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_invalid_token(self, auth_service, mock_jwt_auth):
        mock_jwt_auth.verify_token.return_value = None

        with pytest.raises(InvalidUserToken):
            await auth_service.validate("invalid_token")

    @pytest.mark.asyncio
    async def test_validate_user_not_found(
        self, auth_service, mock_user_repo, mock_jwt_auth, test_user
    ):
        mock_jwt_auth.verify_token.return_value = TokenPayload(uuid=test_user.uuid)
        mock_user_repo.get_user_by_uuid.return_value = None

        with pytest.raises(InvalidUserToken):
            await auth_service.validate("valid_token")


class TestAuthServiceCreateAccessToken:
    def test_create_access_token_generates_jwt(
        self, auth_service, mock_jwt_auth, test_user
    ):
        token = auth_service._create_access_token(test_user.uuid)

        assert token.token == "jwt_token_value"
        mock_jwt_auth.generate_token.assert_called_once()

    def test_create_access_token_payload_contains_uuid(
        self, auth_service, mock_jwt_auth, test_user
    ):
        auth_service._create_access_token(test_user.uuid)

        call_args = mock_jwt_auth.generate_token.call_args
        payload = call_args[0][0]
        assert isinstance(payload, TokenPayload)
        assert payload.uuid == test_user.uuid

    def test_create_access_token_sets_ttl(self, auth_service, mock_jwt_auth):
        user_uuid = uuid4()
        token = auth_service._create_access_token(user_uuid)

        assert token.ttl_seconds == mock_jwt_auth.generate_token.return_value.ttl


class TestAuthServiceIntegration:
    @pytest.mark.asyncio
    async def test_complete_registration_workflow(
        self, auth_service, mock_user_repo, test_user
    ):
        mock_user_repo.add_user.return_value = test_user

        token = await auth_service.add_user("newuser@example.com", "password123")

        assert token.ttl_seconds > 0

    @pytest.mark.asyncio
    async def test_complete_login_workflow(
        self, auth_service, mock_user_repo, mock_hasher, test_user
    ):
        mock_user_repo.get_user_by_email.return_value = test_user
        mock_hasher.verify.return_value = True

        await auth_service.verify_user("test@example.com", "password123")

    @pytest.mark.asyncio
    async def test_token_payload_structure(self):
        user_uuid = uuid4()
        payload = TokenPayload(uuid=user_uuid)

        assert payload.uuid == user_uuid
        assert isinstance(payload.uuid, UUID)


class TestAuthServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_verify_user_handles_repository_error(
        self, auth_service, mock_user_repo
    ):
        mock_user_repo.get_user_by_email.side_effect = UserRepositoryError("DB error")

        with pytest.raises(AuthError):
            await auth_service.verify_user("test@example.com", "password123")

    @pytest.mark.asyncio
    async def test_add_user_handles_existing_user(self, auth_service, mock_user_repo):
        mock_user_repo.add_user.side_effect = UserAlreadyExists()

        with pytest.raises(CannotCreateUser):
            await auth_service.add_user("test@example.com", "password123")
