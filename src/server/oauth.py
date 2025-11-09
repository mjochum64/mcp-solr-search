#!/usr/bin/env python3
"""
OAuth 2.1 authentication and authorization for MCP Server.

This module provides OAuth token validation using Keycloak as the identity provider,
following the MCP Specification 2025-06-18.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from jose import jwt, JWTError, jwk
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

logger = logging.getLogger(__name__)


@dataclass
class OAuth2Config:
    """OAuth 2.1 configuration for Keycloak integration."""

    enabled: bool
    provider: str
    keycloak_url: str
    realm: str
    client_id: str
    client_secret: str
    required_scopes: List[str]
    token_validation_endpoint: str
    jwks_endpoint: str
    # Server-side token retrieval (optional)
    auto_refresh: bool = False
    username: str = ""
    password: str = ""
    token_endpoint: str = ""

    @classmethod
    def from_env(cls) -> "OAuth2Config":
        """Create OAuth configuration from environment variables."""
        enabled = os.getenv("ENABLE_OAUTH", "false").lower() == "true"
        provider = os.getenv("OAUTH_PROVIDER", "keycloak")
        keycloak_url = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
        realm = os.getenv("KEYCLOAK_REALM", "solr-mcp")
        client_id = os.getenv("KEYCLOAK_CLIENT_ID", "solr-search-server")
        client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET", "")

        # Parse scopes from comma-separated list
        scopes_str = os.getenv("OAUTH_SCOPES", "solr:search,solr:read")
        required_scopes = [s.strip() for s in scopes_str.split(",") if s.strip()]

        # Server-side token retrieval
        auto_refresh = os.getenv("OAUTH_AUTO_REFRESH", "false").lower() == "true"
        username = os.getenv("OAUTH_USERNAME", "")
        password = os.getenv("OAUTH_PASSWORD", "")

        # Build endpoints
        token_endpoint = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
        token_validation_endpoint = (
            f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token/introspect"
        )
        jwks_endpoint = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"

        return cls(
            enabled=enabled,
            provider=provider,
            keycloak_url=keycloak_url,
            realm=realm,
            client_id=client_id,
            client_secret=client_secret,
            required_scopes=required_scopes,
            token_validation_endpoint=token_validation_endpoint,
            jwks_endpoint=jwks_endpoint,
            auto_refresh=auto_refresh,
            username=username,
            password=password,
            token_endpoint=token_endpoint,
        )


class TokenValidator:
    """
    Validates OAuth 2.1 access tokens using JWKS and token introspection.

    This validator supports both:
    1. Local JWT validation using JWKS (fast, offline)
    2. Remote token introspection via Keycloak API (authoritative)
    """

    def __init__(self, config: OAuth2Config):
        """
        Initialize the token validator.

        Args:
            config: OAuth 2.1 configuration
        """
        self.config = config
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_expires: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()

    async def _fetch_jwks(self) -> Dict[str, Any]:
        """
        Fetch JWKS (JSON Web Key Set) from Keycloak.

        Caches the result for 1 hour to reduce network calls.

        Returns:
            Dict containing JWKS keys

        Raises:
            Exception: If JWKS fetch fails
        """
        # Check cache
        if (
            self._jwks_cache
            and self._jwks_cache_expires
            and datetime.utcnow() < self._jwks_cache_expires
        ):
            return self._jwks_cache

        # Fetch from Keycloak
        try:
            if not self._http_client:
                self._http_client = httpx.AsyncClient()

            response = await self._http_client.get(self.config.jwks_endpoint)
            response.raise_for_status()

            jwks_data = response.json()

            # Cache for 1 hour
            self._jwks_cache = jwks_data
            self._jwks_cache_expires = datetime.utcnow() + timedelta(hours=1)

            logger.info("JWKS fetched and cached successfully")
            return jwks_data

        except Exception as e:
            logger.error(f"Failed to fetch JWKS from {self.config.jwks_endpoint}: {e}")
            raise

    async def validate_token_local(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token locally using JWKS.

        This is fast but doesn't check if the token was revoked.

        Args:
            token: JWT access token

        Returns:
            Dict containing decoded token claims

        Raises:
            JWTError: If token is invalid
            ExpiredSignatureError: If token is expired
        """
        try:
            # Fetch JWKS
            jwks = await self._fetch_jwks()

            # Decode token header to get key ID (kid)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise JWTError("Token header missing 'kid' field")

            # Find matching key in JWKS
            key_data = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    key_data = key
                    break

            if not key_data:
                raise JWTError(f"No matching key found in JWKS for kid: {kid}")

            # Construct RSA public key from JWKS
            public_key = jwk.construct(key_data)

            # Verify and decode token
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience="account",  # Keycloak default audience
                issuer=f"{self.config.keycloak_url}/realms/{self.config.realm}",
            )

            logger.debug("Token validated locally using JWKS")
            return claims

        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise

    async def validate_token_introspection(self, token: str) -> Dict[str, Any]:
        """
        Validate token using Keycloak's introspection endpoint.

        This is authoritative and checks token revocation, but slower.

        Args:
            token: JWT access token

        Returns:
            Dict containing introspection response

        Raises:
            Exception: If introspection fails or token is inactive
        """
        try:
            if not self._http_client:
                self._http_client = httpx.AsyncClient()

            response = await self._http_client.post(
                self.config.token_validation_endpoint,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=(self.config.client_id, self.config.client_secret),
                data={"token": token},
            )
            response.raise_for_status()

            introspection = response.json()

            # Check if token is active
            if not introspection.get("active", False):
                raise Exception("Token is not active (revoked or expired)")

            logger.debug("Token validated via introspection endpoint")
            return introspection

        except Exception as e:
            logger.error(f"Token introspection failed: {e}")
            raise

    async def validate_token(
        self, token: str, use_introspection: bool = False
    ) -> Dict[str, Any]:
        """
        Validate access token using the configured method.

        Args:
            token: JWT access token from Authorization header
            use_introspection: If True, use introspection endpoint (slower but authoritative)
                             If False, use local JWKS validation (faster)

        Returns:
            Dict containing token claims/introspection data

        Raises:
            Exception: If token is invalid
        """
        if not self.config.enabled:
            logger.warning("OAuth is disabled, skipping token validation")
            return {"sub": "anonymous", "scope": "all"}

        if use_introspection:
            return await self.validate_token_introspection(token)
        else:
            return await self.validate_token_local(token)

    async def retrieve_token(self, username: str, password: str) -> Dict[str, Any]:
        """
        Retrieve OAuth access token using Resource Owner Password Credentials Grant.

        This method allows the MCP server to obtain a token on behalf of a user
        for server-side token management.

        Args:
            username: Username for authentication
            password: Password for authentication

        Returns:
            Dict containing access_token, token_type, expires_in, refresh_token, scope

        Raises:
            Exception: If token retrieval fails
        """
        try:
            if not self._http_client:
                self._http_client = httpx.AsyncClient()

            # Prepare request
            data = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "username": username,
                "password": password,
                "grant_type": "password",
                "scope": " ".join(self.config.required_scopes),
            }

            logger.info(
                f"Retrieving OAuth token from {self.config.token_endpoint} for user '{username}'"
            )

            response = await self._http_client.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

            token_data = response.json()

            logger.info(
                f"OAuth token retrieved successfully, expires in {token_data.get('expires_in')} seconds"
            )
            return token_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to retrieve OAuth token (HTTP {e.response.status_code}): {e.response.text}"
            )
            raise Exception(f"OAuth token retrieval failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to retrieve OAuth token: {e}")
            raise

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh OAuth access token using refresh token.

        Args:
            refresh_token: Refresh token from previous token retrieval

        Returns:
            Dict containing new access_token, token_type, expires_in, refresh_token, scope

        Raises:
            Exception: If token refresh fails
        """
        try:
            if not self._http_client:
                self._http_client = httpx.AsyncClient()

            # Prepare request
            data = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }

            logger.debug(f"Refreshing OAuth token at {self.config.token_endpoint}")

            response = await self._http_client.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

            token_data = response.json()

            logger.info(
                f"OAuth token refreshed successfully, expires in {token_data.get('expires_in')} seconds"
            )
            return token_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to refresh OAuth token (HTTP {e.response.status_code}): {e.response.text}"
            )
            raise Exception(f"OAuth token refresh failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {e}")
            raise

    def check_scopes(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if token contains required scopes.

        Args:
            token_data: Decoded token claims or introspection response

        Returns:
            True if all required scopes are present, False otherwise
        """
        # Extract scopes from token
        token_scope = token_data.get("scope", "")
        if isinstance(token_scope, str):
            token_scopes = set(token_scope.split())
        elif isinstance(token_scope, list):
            token_scopes = set(token_scope)
        else:
            token_scopes = set()

        # Check if all required scopes are present
        required_scopes = set(self.config.required_scopes)
        missing_scopes = required_scopes - token_scopes

        if missing_scopes:
            logger.warning(
                f"Token missing required scopes: {missing_scopes}. "
                f"Has: {token_scopes}, Requires: {required_scopes}"
            )
            return False

        logger.debug(f"Token has all required scopes: {required_scopes}")
        return True


class OAuthError(Exception):
    """Base exception for OAuth-related errors."""

    pass


class TokenMissingError(OAuthError):
    """Raised when Authorization header is missing."""

    pass


class TokenInvalidError(OAuthError):
    """Raised when token validation fails."""

    pass


class InsufficientScopesError(OAuthError):
    """Raised when token doesn't have required scopes."""

    pass
