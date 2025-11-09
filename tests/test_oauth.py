"""
Unit tests for OAuth 2.1 authentication.

These tests verify the OAuth configuration, token validation, and scope checking
without requiring a running Keycloak instance.
"""
import os
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path
import sys
from pathlib import Path

project_root = str(Path(__file__).parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.server.oauth import (
    OAuth2Config,
    TokenValidator,
    OAuthError,
    TokenMissingError,
    TokenInvalidError,
    InsufficientScopesError,
)


@pytest.fixture
def mock_env_oauth_enabled(monkeypatch):
    """Mock environment variables with OAuth enabled."""
    monkeypatch.setenv("ENABLE_OAUTH", "true")
    monkeypatch.setenv("OAUTH_PROVIDER", "keycloak")
    monkeypatch.setenv("KEYCLOAK_URL", "http://localhost:8080")
    monkeypatch.setenv("KEYCLOAK_REALM", "solr-mcp")
    monkeypatch.setenv("KEYCLOAK_CLIENT_ID", "solr-search-server")
    monkeypatch.setenv("KEYCLOAK_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("OAUTH_SCOPES", "solr:search,solr:read")


@pytest.fixture
def mock_env_oauth_disabled(monkeypatch):
    """Mock environment variables with OAuth disabled."""
    monkeypatch.setenv("ENABLE_OAUTH", "false")


@pytest.fixture
def oauth_config_enabled(mock_env_oauth_enabled):
    """Create OAuth config with OAuth enabled."""
    return OAuth2Config.from_env()


@pytest.fixture
def oauth_config_disabled(mock_env_oauth_disabled):
    """Create OAuth config with OAuth disabled."""
    return OAuth2Config.from_env()


@pytest.fixture
def mock_jwks():
    """Mock JWKS response from Keycloak."""
    return {
        "keys": [
            {
                "kid": "test-key-id",
                "kty": "RSA",
                "use": "sig",
                "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
                "e": "AQAB",
            }
        ]
    }


@pytest.fixture
def mock_token_claims():
    """Mock decoded token claims."""
    return {
        "exp": int((datetime.utcnow() + timedelta(minutes=5)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "jti": "test-jti",
        "iss": "http://localhost:8080/realms/solr-mcp",
        "aud": "account",
        "sub": "test-user-id",
        "typ": "Bearer",
        "azp": "solr-search-server",
        "scope": "solr:search solr:read",
        "preferred_username": "testuser",
        "email": "testuser@example.com",
    }


@pytest.fixture
def mock_introspection_response():
    """Mock introspection response from Keycloak."""
    return {
        "active": True,
        "exp": int((datetime.utcnow() + timedelta(minutes=5)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "username": "testuser",
        "scope": "solr:search solr:read",
        "client_id": "solr-search-server",
    }


class TestOAuth2Config:
    """Tests for OAuth2Config class."""

    def test_config_from_env_enabled(self, oauth_config_enabled):
        """Test OAuth config loading when enabled."""
        assert oauth_config_enabled.enabled is True
        assert oauth_config_enabled.provider == "keycloak"
        assert oauth_config_enabled.keycloak_url == "http://localhost:8080"
        assert oauth_config_enabled.realm == "solr-mcp"
        assert oauth_config_enabled.client_id == "solr-search-server"
        assert oauth_config_enabled.client_secret == "test-secret"
        assert oauth_config_enabled.required_scopes == ["solr:search", "solr:read"]

    def test_config_from_env_disabled(self, oauth_config_disabled):
        """Test OAuth config loading when disabled."""
        assert oauth_config_disabled.enabled is False

    def test_endpoints_constructed_correctly(self, oauth_config_enabled):
        """Test that OAuth endpoints are constructed correctly."""
        expected_introspect = (
            "http://localhost:8080/realms/solr-mcp/protocol/openid-connect/token/introspect"
        )
        expected_jwks = (
            "http://localhost:8080/realms/solr-mcp/protocol/openid-connect/certs"
        )
        assert oauth_config_enabled.token_validation_endpoint == expected_introspect
        assert oauth_config_enabled.jwks_endpoint == expected_jwks


class TestTokenValidator:
    """Tests for TokenValidator class."""

    @pytest.mark.asyncio
    async def test_fetch_jwks_success(self, oauth_config_enabled, mock_jwks):
        """Test successful JWKS fetching."""
        validator = TokenValidator(oauth_config_enabled)

        # Mock HTTP client
        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_jwks)
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        validator._http_client = mock_client

        jwks = await validator._fetch_jwks()

        assert jwks == mock_jwks
        mock_client.get.assert_called_once_with(oauth_config_enabled.jwks_endpoint)

    @pytest.mark.asyncio
    async def test_fetch_jwks_caching(self, oauth_config_enabled, mock_jwks):
        """Test that JWKS is cached and not fetched multiple times."""
        validator = TokenValidator(oauth_config_enabled)

        # Mock HTTP client
        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_jwks)
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        validator._http_client = mock_client

        # First fetch
        jwks1 = await validator._fetch_jwks()
        # Second fetch (should use cache)
        jwks2 = await validator._fetch_jwks()

        assert jwks1 == jwks2
        # Should only call get() once due to caching
        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_validate_token_introspection_success(
        self, oauth_config_enabled, mock_introspection_response
    ):
        """Test successful token validation via introspection."""
        validator = TokenValidator(oauth_config_enabled)

        # Mock HTTP client
        mock_response = Mock()
        mock_response.json = Mock(return_value=mock_introspection_response)
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        validator._http_client = mock_client

        result = await validator.validate_token_introspection("fake-token")

        assert result["active"] is True
        assert result["username"] == "testuser"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_token_introspection_inactive(
        self, oauth_config_enabled
    ):
        """Test token validation with inactive token."""
        validator = TokenValidator(oauth_config_enabled)

        # Mock HTTP client with inactive token
        mock_response = Mock()
        mock_response.json = Mock(return_value={"active": False})
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        validator._http_client = mock_client

        with pytest.raises(Exception, match="not active"):
            await validator.validate_token_introspection("fake-token")

    @pytest.mark.asyncio
    async def test_validate_token_oauth_disabled(self, oauth_config_disabled):
        """Test that validation is skipped when OAuth is disabled."""
        validator = TokenValidator(oauth_config_disabled)

        result = await validator.validate_token("any-token")

        assert result["sub"] == "anonymous"
        assert result["scope"] == "all"

    def test_check_scopes_success(self, oauth_config_enabled, mock_token_claims):
        """Test successful scope checking."""
        validator = TokenValidator(oauth_config_enabled)

        # Token has all required scopes
        assert validator.check_scopes(mock_token_claims) is True

    def test_check_scopes_missing(self, oauth_config_enabled, mock_token_claims):
        """Test scope checking with missing scopes."""
        validator = TokenValidator(oauth_config_enabled)

        # Token is missing required scopes
        mock_token_claims["scope"] = "solr:search"  # Missing solr:read

        assert validator.check_scopes(mock_token_claims) is False

    def test_check_scopes_list_format(self, oauth_config_enabled):
        """Test scope checking with scopes as list."""
        validator = TokenValidator(oauth_config_enabled)

        token_data = {"scope": ["solr:search", "solr:read", "extra:scope"]}

        assert validator.check_scopes(token_data) is True

    def test_check_scopes_empty(self, oauth_config_enabled):
        """Test scope checking with no scopes in token."""
        validator = TokenValidator(oauth_config_enabled)

        token_data = {"scope": ""}

        assert validator.check_scopes(token_data) is False


class TestOAuthExceptions:
    """Tests for OAuth exception classes."""

    def test_oauth_error_inheritance(self):
        """Test that custom exceptions inherit from OAuthError."""
        assert issubclass(TokenMissingError, OAuthError)
        assert issubclass(TokenInvalidError, OAuthError)
        assert issubclass(InsufficientScopesError, OAuthError)

    def test_exception_messages(self):
        """Test exception messages."""
        try:
            raise TokenMissingError("Test message")
        except TokenMissingError as e:
            assert str(e) == "Test message"

        try:
            raise TokenInvalidError("Invalid token")
        except TokenInvalidError as e:
            assert str(e) == "Invalid token"

        try:
            raise InsufficientScopesError("Missing scopes")
        except InsufficientScopesError as e:
            assert str(e) == "Missing scopes"
