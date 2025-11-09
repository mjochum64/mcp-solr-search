#!/usr/bin/env python3
"""
Haupt-MCP-Server für Apache Solr-Dokumentensuche.

Diese Implementierung stellt MCP-Ressourcen und -Tools für die Solr-Integration bereit,
optimiert für die Verwendung mit dem MCP-Protokoll durch LLMs.
"""
import os
import json
import sys
import logging
import traceback
from typing import Dict, List, Optional, Any, AsyncIterator
from pathlib import Path
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context

# Projektpfad zum System-Pfad hinzufügen, um absolute Imports zu ermöglichen
# Dadurch können wir den Server mit 'mcp dev' und 'python run_server.py' ausführen
project_dir = str(
    Path(__file__).parents[2]
)  # Zwei Ebenen nach oben: src/server -> src -> Projektwurzel
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    print(f"Added {project_dir} to system path")

# Importiere lokale Module
from src.server.models import SearchParams, GetDocumentParams
from src.server.solr_client import SolrClient
from src.server.oauth import (
    OAuth2Config,
    TokenValidator,
    OAuthError,
    TokenMissingError,
    TokenInvalidError,
    InsufficientScopesError,
)

# Logger für diese Datei konfigurieren
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-server")

# Umgebungsvariablen laden
load_dotenv()

# MCP-Server-Konfiguration
MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "Solr Search")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))

# Solr-Verbindungskonfiguration
SOLR_BASE_URL = os.getenv("SOLR_BASE_URL", "http://localhost:8983/solr")
SOLR_COLLECTION = os.getenv("SOLR_COLLECTION", "documents")
SOLR_USERNAME = os.getenv("SOLR_USERNAME", "")
SOLR_PASSWORD = os.getenv("SOLR_PASSWORD", "")


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    solr_client: SolrClient
    oauth_config: OAuth2Config
    token_validator: Optional[TokenValidator] = None


# Lifespan Context Manager für proper state management
@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize and cleanup resources for the MCP server with type-safe context."""
    logger.info("Initializing MCP server resources...")

    # Initialize Solr client during startup
    solr_client = SolrClient(
        base_url=SOLR_BASE_URL,
        collection=SOLR_COLLECTION,
        username=SOLR_USERNAME,
        password=SOLR_PASSWORD,
    )
    logger.info("Solr client initialized")

    # Initialize OAuth configuration
    oauth_config = OAuth2Config.from_env()
    if oauth_config.enabled:
        logger.info(
            f"OAuth 2.1 enabled with provider: {oauth_config.provider} "
            f"(realm: {oauth_config.realm})"
        )
        logger.info(f"Required scopes: {oauth_config.required_scopes}")
    else:
        logger.info("OAuth 2.1 is disabled")

    # Initialize token validator if OAuth is enabled
    token_validator = None
    if oauth_config.enabled:
        token_validator = TokenValidator(oauth_config)
        async with token_validator:
            # Test JWKS fetch
            try:
                await token_validator._fetch_jwks()
                logger.info("JWKS fetched successfully - OAuth is ready")
            except Exception as e:
                logger.warning(f"Failed to fetch JWKS: {e}")
                logger.warning("OAuth validation may fail until Keycloak is accessible")

    # Test Solr connection
    await test_solr_connection(solr_client)

    try:
        yield AppContext(
            solr_client=solr_client,
            oauth_config=oauth_config,
            token_validator=token_validator,
        )
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down MCP server")
        if token_validator and token_validator._http_client:
            await token_validator._http_client.aclose()


# MCP-Server with modern lifespan management
app = FastMCP(MCP_SERVER_NAME, lifespan=lifespan)


async def validate_oauth_token(
    ctx: Context, token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Validate OAuth token if OAuth is enabled.

    Args:
        ctx: MCP context with access to lifespan context
        token: Optional OAuth token (for HTTP transport)

    Returns:
        Dict with token claims if validation succeeds, None if OAuth is disabled

    Raises:
        TokenMissingError: If OAuth is enabled but token is missing
        TokenInvalidError: If token validation fails
        InsufficientScopesError: If token doesn't have required scopes
    """
    app_context = ctx.request_context.lifespan_context

    # Skip validation if OAuth is disabled
    if not app_context.oauth_config.enabled:
        return None

    # Check if token is provided
    if not token:
        # For HTTP transport, token should be in Authorization header
        # For stdio transport (Claude Desktop), OAuth might not apply
        # For now, we'll raise an error if token is missing and OAuth is enabled
        raise TokenMissingError(
            "OAuth is enabled but no access token provided. "
            "Include token in Authorization header: Bearer <token>"
        )

    # Validate token
    try:
        token_data = await app_context.token_validator.validate_token(token)
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise TokenInvalidError(f"Invalid access token: {str(e)}")

    # Check scopes
    if not app_context.token_validator.check_scopes(token_data):
        required = app_context.oauth_config.required_scopes
        raise InsufficientScopesError(
            f"Token missing required scopes. Required: {required}"
        )

    # Log successful authentication
    username = token_data.get("preferred_username", "unknown")
    await ctx.info(f"Authenticated user: {username}")

    return token_data


@app.resource("solr://search/{query}")
async def search_solr(ctx: Context, query: str) -> str:
    """
    Einfache Ressource für die Suche in Solr-Dokumenten.

    Diese Ressource bietet eine einfache Schnittstelle für Solr-Suchen
    über den MCP-Protokoll-Ressourcenmechanismus.

    Note: This resource does not support OAuth authentication. For OAuth-protected
    access, use the 'search' tool instead.

    Args:
        ctx (Context): MCP context with access to lifespan context
        query (str): Die Suchanfrage

    Returns:
        str: JSON-String mit Suchergebnissen
    """
    try:
        # Check if OAuth is enabled - if so, recommend using the tool instead
        app_context = ctx.request_context.lifespan_context
        if app_context.oauth_config.enabled:
            await ctx.warning(
                "OAuth is enabled but this resource doesn't support authentication. "
                "Please use the 'search' tool instead for OAuth-protected access."
            )

        await ctx.info(f"Verarbeite Suchanfrage mit Query: {query}")
        solr_client = ctx.request_context.lifespan_context.solr_client
        results = await solr_client.search(query)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Fehler in search_solr-Ressource: {e}")
        logger.error(traceback.format_exc())
        return json.dumps(
            {"error": f"Fehler bei der Verarbeitung der Suche: {str(e)}"}, indent=2
        )


@app.tool(
    annotations={
        "title": "Search Solr Documents",
        "readOnlyHint": True,
        "description": "Advanced search with filtering, sorting, pagination, faceting, and highlighting (OAuth required if enabled)",
    }
)
async def search(
    query: str,
    filter_query: Optional[str] = None,
    sort: Optional[str] = None,
    rows: int = 10,
    start: int = 0,
    facet_fields: Optional[List[str]] = None,
    highlight_fields: Optional[List[str]] = None,
    access_token: Optional[str] = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Tool für erweiterte Dokumentensuche.

    Dieses Tool bietet eine erweiterte Suchfunktionalität mit Filtern,
    Sortierung, Paginierung, Faceted Search und Highlighting für Solr-Dokumente.

    Args:
        query (str): Solr query string (e.g., "*:*" for all documents)
        filter_query (Optional[str]): Filter query to narrow results
        sort (Optional[str]): Sort order (e.g., "date desc")
        rows (int): Number of results to return (default: 10)
        start (int): Offset for pagination (default: 0)
        facet_fields (Optional[List[str]]): Fields to facet on (e.g., ["category", "author"])
        highlight_fields (Optional[List[str]]): Fields to highlight search terms in (e.g., ["title", "content"])
        access_token (Optional[str]): OAuth 2.1 access token (required if OAuth is enabled)
        ctx (Context): MCP context with access to lifespan context

    Returns:
        Dict[str, Any]: Suchergebnisse (inkl. facet_counts und highlighting wenn angegeben) oder Fehlermeldung
    """
    try:
        # Validate OAuth token if enabled
        try:
            await validate_oauth_token(ctx, access_token)
        except OAuthError as e:
            return {"error": f"Authentication failed: {str(e)}"}

        facet_info = f" mit Facets: {facet_fields}" if facet_fields else ""
        highlight_info = f" mit Highlighting: {highlight_fields}" if highlight_fields else ""
        await ctx.info(f"Verarbeite search-Tool-Anfrage: {query}{facet_info}{highlight_info}")

        solr_client = ctx.request_context.lifespan_context.solr_client
        results = await solr_client.search(
            query=query, filter_query=filter_query, sort=sort, rows=rows, start=start,
            facet_fields=facet_fields, highlight_fields=highlight_fields
        )

        return results
    except Exception as e:
        logger.error(f"Fehler im search-Tool: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Fehler bei der Verarbeitung der Suche: {str(e)}"}


@app.tool(
    annotations={
        "title": "Get Solr Document by ID",
        "readOnlyHint": True,
        "description": "Retrieve a specific document by its ID with optional field selection (OAuth required if enabled)",
    }
)
async def get_document(
    id: str,
    fields: Optional[List[str]] = None,
    access_token: Optional[str] = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Tool zum Abrufen spezifischer Dokumente.

    Dieses Tool ermöglicht das Abrufen von Dokumenten nach ID mit optionaler
    Feldauswahl.

    Args:
        id (str): Document ID to retrieve
        fields (Optional[List[str]]): List of fields to return (default: all fields)
        access_token (Optional[str]): OAuth 2.1 access token (required if OAuth is enabled)
        ctx (Context): MCP context with access to lifespan context

    Returns:
        Dict[str, Any]: Das abgerufene Dokument oder Fehlermeldung
    """
    try:
        # Validate OAuth token if enabled
        try:
            await validate_oauth_token(ctx, access_token)
        except OAuthError as e:
            return {"error": f"Authentication failed: {str(e)}"}

        await ctx.info(f"Verarbeite get_document-Tool-Anfrage für ID: {id}")

        solr_client = ctx.request_context.lifespan_context.solr_client
        document = await solr_client.get_document(doc_id=id, fields=fields)

        return document
    except Exception as e:
        logger.error(f"Fehler im get_document-Tool: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Fehler beim Abrufen des Dokuments: {str(e)}"}


async def test_solr_connection(solr_client: SolrClient):
    """
    Testet die Verbindung zum Solr-Server vor dem Start des MCP-Servers.

    Args:
        solr_client (SolrClient): The Solr client instance to test

    Returns:
        bool: True, wenn die Verbindung erfolgreich war, sonst False
    """
    try:
        logger.info("Teste Solr-Verbindung...")
        async with httpx.AsyncClient() as client:
            ping_url = f"{solr_client.base_url}/{solr_client.collection}/admin/ping"
            response = await client.get(ping_url)
            response.raise_for_status()
            logger.info("Solr-Verbindung erfolgreich")
        return True
    except Exception as e:
        logger.warning(f"Solr-Verbindungstest fehlgeschlagen: {e}")
        logger.warning("Server wird gestartet, aber Solr-Suchen könnten fehlschlagen")
        return False


if __name__ == "__main__":
    # Umgebungsvariablen für den MCP-Server setzen
    os.environ["MCP_PORT"] = str(MCP_SERVER_PORT)

    import asyncio

    # Solr-Verbindung wird im Lifespan-Kontext getestet

    try:
        # Server starten mit modernem FastMCP
        logger.info(
            f"Starte MCP-Server '{MCP_SERVER_NAME}' auf Port {MCP_SERVER_PORT}..."
        )
        print(
            f"MCP-Server wird gestartet, nutze 'mcp dev {__file__}' für die Entwicklungsumgebung"
        )
        print("Server unterstützt sowohl MCP-Protokoll als auch HTTP-Transport")
        # Test available transports
        if len(sys.argv) > 1 and sys.argv[1] == "--http":
            print("Starting server with Streamable HTTP transport...")
            app.run(transport="streamable-http")
        elif len(sys.argv) > 1 and sys.argv[1] == "--sse":
            print("Starting server with SSE transport...")
            app.run(transport="sse")
        else:
            app.run(transport="stdio")
    except Exception as e:
        logger.error(f"Fehler beim Starten des Servers: {e}")
        logger.error(traceback.format_exc())
