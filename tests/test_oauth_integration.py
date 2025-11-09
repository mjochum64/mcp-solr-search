"""
Integration tests for OAuth 2.1 authentication with real Keycloak.

These tests require:
- Keycloak running at localhost:8080
- Realm 'solr-mcp' configured
- Client 'solr-search-server' configured
- Test user 'testuser' with password 'testpassword'

Run setup-keycloak.sh first to configure Keycloak automatically.
"""
import os
import pytest
import pytest_asyncio
import httpx
from unittest.mock import AsyncMock
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
    TokenMissingError,
    TokenInvalidError,
    InsufficientScopesError,
)


# Check if Keycloak is available
def is_keycloak_available():
    """Check if Keycloak is running and accessible."""
    try:
        response = httpx.get("http://localhost:8080", timeout=2)
        return response.status_code == 200
    except:
        return False


# Skip all tests if Keycloak is not available
pytestmark = pytest.mark.skipif(
    not is_keycloak_available(),
    reason="Keycloak not available at localhost:8080. Run: docker-compose up -d keycloak",
)


@pytest.fixture
def oauth_config():
    """OAuth configuration for integration tests."""
    # Read client secret from environment or use default from setup-keycloak.sh
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET", "w9ynv6VG4yfM86x6XTwjB1RBrrpkEt6b")

    return OAuth2Config(
        enabled=True,
        provider="keycloak",
        keycloak_url="http://localhost:8080",
        realm="solr-mcp",
        client_id="solr-search-server",
        client_secret=client_secret,
        required_scopes=["solr:search", "solr:read"],
        token_validation_endpoint="http://localhost:8080/realms/solr-mcp/protocol/openid-connect/token/introspect",
        jwks_endpoint="http://localhost:8080/realms/solr-mcp/protocol/openid-connect/certs",
    )


@pytest_asyncio.fixture
async def valid_access_token(oauth_config):
    """Get a valid access token from Keycloak."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{oauth_config.keycloak_url}/realms/{oauth_config.realm}/protocol/openid-connect/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": oauth_config.client_id,
                "client_secret": oauth_config.client_secret,
                "username": "testuser",
                "password": "testpassword",
                "grant_type": "password",
                "scope": "solr:search solr:read",
            },
        )

        if response.status_code != 200:
            pytest.skip(
                f"Failed to get access token from Keycloak. "
                f"Status: {response.status_code}, Response: {response.text}"
            )

        token_data = response.json()
        return token_data["access_token"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestKeycloakIntegration:
    """Integration tests with real Keycloak instance."""

    async def test_fetch_jwks_from_keycloak(self, oauth_config):
        """Test fetching JWKS from real Keycloak."""
        validator = TokenValidator(oauth_config)

        async with validator:
            jwks = await validator._fetch_jwks()

            assert "keys" in jwks
            assert len(jwks["keys"]) > 0
            assert "kid" in jwks["keys"][0]
            assert "kty" in jwks["keys"][0]

    async def test_validate_token_with_jwks(self, oauth_config, valid_access_token):
        """Test token validation using JWKS with real Keycloak token."""
        validator = TokenValidator(oauth_config)

        async with validator:
            # Validate using local JWKS
            token_data = await validator.validate_token(
                valid_access_token, use_introspection=False
            )

            assert "sub" in token_data
            assert "preferred_username" in token_data
            assert token_data["preferred_username"] == "testuser"
            assert "scope" in token_data

    async def test_validate_token_with_introspection(
        self, oauth_config, valid_access_token
    ):
        """Test token validation using introspection with real Keycloak."""
        validator = TokenValidator(oauth_config)

        async with validator:
            # Validate using introspection endpoint
            introspection = await validator.validate_token(
                valid_access_token, use_introspection=True
            )

            assert introspection["active"] is True
            assert introspection["username"] == "testuser"
            assert "scope" in introspection

    async def test_validate_invalid_token(self, oauth_config):
        """Test that invalid tokens are rejected."""
        validator = TokenValidator(oauth_config)

        async with validator:
            with pytest.raises(Exception):
                await validator.validate_token("invalid-token-xyz")

    async def test_validate_expired_token(self, oauth_config):
        """Test that expired tokens are rejected."""
        # This is a token that is structurally valid but expired
        expired_token = (
            "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJSdk9FcFUyazRIUGx3V29"
            "Ybl91dWtMU0o4YlJIbFNkNWwtMXRWR2cxaWZVIn0.eyJleHAiOjE2MDAwMDAwMDAsImlhdC"
            "I6MTYwMDAwMDAwMCwianRpIjoiZXhwaXJlZC10b2tlbiIsImlzcyI6Imh0dHA6Ly9sb2Nh"
            "bGhvc3Q6ODA4MC9yZWFsbXMvc29sci1tY3AiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoidG"
            "VzdC11c2VyIiwidHlwIjoiQmVhcmVyIn0.invalid-signature"
        )

        validator = TokenValidator(oauth_config)

        async with validator:
            with pytest.raises(Exception):
                await validator.validate_token(expired_token)

    async def test_scope_validation(self, oauth_config, valid_access_token):
        """Test that tokens are checked for required scopes."""
        validator = TokenValidator(oauth_config)

        async with validator:
            # Get token data
            token_data = await validator.validate_token(
                valid_access_token, use_introspection=True
            )

            # Check scopes
            has_scopes = validator.check_scopes(token_data)
            assert has_scopes is True

    async def test_missing_scopes_detection(self, oauth_config):
        """Test detection of missing required scopes."""
        # Create config that requires a scope the token doesn't have
        strict_config = OAuth2Config(
            enabled=True,
            provider="keycloak",
            keycloak_url=oauth_config.keycloak_url,
            realm=oauth_config.realm,
            client_id=oauth_config.client_id,
            client_secret=oauth_config.client_secret,
            required_scopes=["solr:search", "solr:read", "solr:admin"],  # admin scope not granted
            token_validation_endpoint=oauth_config.token_validation_endpoint,
            jwks_endpoint=oauth_config.jwks_endpoint,
        )

        validator = TokenValidator(strict_config)

        async with httpx.AsyncClient() as client:
            # Get token with only solr:search and solr:read scopes
            response = await client.post(
                f"{oauth_config.keycloak_url}/realms/{oauth_config.realm}/protocol/openid-connect/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_id": oauth_config.client_id,
                    "client_secret": oauth_config.client_secret,
                    "username": "testuser",
                    "password": "testpassword",
                    "grant_type": "password",
                    "scope": "solr:search solr:read",  # Not requesting solr:admin
                },
            )

            token = response.json()["access_token"]

            async with validator:
                token_data = await validator.validate_token(token, use_introspection=True)

                # Should fail scope check
                has_scopes = validator.check_scopes(token_data)
                assert has_scopes is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPServerOAuthIntegration:
    """Integration tests for MCP server with OAuth enabled."""

    async def test_search_tool_with_valid_token(self, oauth_config, valid_access_token):
        """Test search tool with valid OAuth token."""
        from src.server.mcp_server import search
        from src.server.solr_client import SolrClient

        # Mock context with OAuth enabled
        context = AsyncMock()

        # Create mock Solr client
        mock_solr_client = AsyncMock()
        mock_solr_client.search.return_value = {
            "responseHeader": {"status": 0},
            "response": {"numFound": 0, "start": 0, "docs": []},
        }

        # Setup context
        context.request_context.lifespan_context.solr_client = mock_solr_client
        context.request_context.lifespan_context.oauth_config = oauth_config

        # Create validator
        validator = TokenValidator(oauth_config)
        async with validator:
            context.request_context.lifespan_context.token_validator = validator

            context.info = AsyncMock()
            context.debug = AsyncMock()
            context.warning = AsyncMock()
            context.error = AsyncMock()

            # Call search tool with valid token
            result = await search(
                query="*:*",
                access_token=valid_access_token,
                ctx=context,
            )

            # Should succeed
            assert "error" not in result
            assert "response" in result

    async def test_search_tool_without_token(self, oauth_config):
        """Test search tool without token when OAuth is enabled."""
        from src.server.mcp_server import search

        # Mock context with OAuth enabled
        context = AsyncMock()

        mock_solr_client = AsyncMock()
        context.request_context.lifespan_context.solr_client = mock_solr_client
        context.request_context.lifespan_context.oauth_config = oauth_config

        validator = TokenValidator(oauth_config)
        async with validator:
            context.request_context.lifespan_context.token_validator = validator

            context.info = AsyncMock()

            # Call search tool without token
            result = await search(
                query="*:*",
                access_token=None,  # No token provided
                ctx=context,
            )

            # Should fail with authentication error
            assert "error" in result
            assert "Authentication failed" in result["error"]

    async def test_search_tool_with_invalid_token(self, oauth_config):
        """Test search tool with invalid token."""
        from src.server.mcp_server import search

        # Mock context with OAuth enabled
        context = AsyncMock()

        mock_solr_client = AsyncMock()
        context.request_context.lifespan_context.solr_client = mock_solr_client
        context.request_context.lifespan_context.oauth_config = oauth_config

        validator = TokenValidator(oauth_config)
        async with validator:
            context.request_context.lifespan_context.token_validator = validator

            context.info = AsyncMock()

            # Call search tool with invalid token
            result = await search(
                query="*:*",
                access_token="invalid-token-12345",
                ctx=context,
            )

            # Should fail with authentication error
            assert "error" in result
            assert "Authentication failed" in result["error"]
