# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) Server for Apache Solr Document Search that bridges LLMs with Solr search capabilities. The project has been fully modernized to **MCP 1.21.0** (2025-06-18 specification), featuring:
- Modern lifespan context management
- Streamable HTTP transport (native support)
- Tool annotations for enhanced client integration
- Context-based state management
- **edismax Multi-Field Search** (v1.5.0) - Automatic search across title, content, author, category
- **OAuth 2.1 with Auto-Refresh** (v1.5.0) - Server-side token management, no manual tokens needed

## Essential Commands

### Environment Setup
```bash
# Install dependencies (virtual environment must be activated)
uv install                # Preferred
pip install -e .         # Alternative

# Start Solr development environment
./start_solr.sh          # Includes sample data loading
```

### Development Servers
```bash
# MCP server for LLM integration
python run_server.py --mode mcp

# HTTP server for direct access (MCP 1.6.0 workaround)
python run_server.py --mode http

# MCP development server with inspector GUI
mcp dev src/server/mcp_server.py
```

### Testing
```bash
# Run all tests
pytest

# Unit tests only (with mocked Solr)
pytest tests/test_server.py

# Integration tests (requires running Solr)
pytest tests/test_integration_server.py -m integration

# Run specific test
pytest tests/test_server.py::test_search_solr_resource -v

# Coverage reporting
pytest --cov=src
```

### Code Quality
```bash
# Format and lint (required before commits)
black src/ tests/ && flake8 src/ tests/
```

## High-Level Architecture

### Modern MCP Architecture
The project uses a unified MCP server architecture with native transport support:

**MCP Server** (`src/server/mcp_server.py`): Modern FastMCP-based server with:
- **Lifespan Context Manager**: Type-safe dependency injection with `AppContext` dataclass
- **Multiple Transports**: Native support for stdio, SSE, and Streamable HTTP
- **Tool Annotations**: Enhanced metadata with `readOnlyHint` for better client UX
- **Context-Based Logging**: Direct client communication via `ctx.info/debug/warning/error`

**HTTP Server** (`src/server/http_server.py`): Legacy FastAPI-based workaround (no longer required with MCP 1.21.0)

### Core Components

**SolrClient** (`src/server/solr_client.py`): Async HTTP client managing all Solr communication with error handling and connection management.

**Data Models** (`src/server/models.py`): Pydantic models providing type safety for search parameters, document retrieval, and error responses.

**Entry Point** (`src/main.py`): CLI argument parsing that routes to appropriate server mode, with `run_server.py` as convenience wrapper.

**OAuth Module** (`src/server/oauth.py`): OAuth 2.1 authentication with Keycloak, featuring:
- Token validation via JWKS (fast, cached) and introspection (authoritative)
- Server-side token retrieval with Password Grant flow
- Automatic token refresh background task (every 4 minutes)
- Fine-grained scope checking (solr:search, solr:read, solr:write, solr:admin)

### v1.5.0 Features

**edismax Multi-Field Search** (`SolrClient.search()`):
- Automatically searches across: title^2 (boosted), content^1.5, author, category
- Minimum match: 75% of search terms must match
- Fixes issue where simple queries like "machine learning" found 0 documents
- Field-specific queries (with `:`) still work without edismax

**OAuth Auto-Refresh** (`.env` configuration):
```bash
OAUTH_AUTO_REFRESH=true
OAUTH_USERNAME=testuser
OAUTH_PASSWORD=testpassword
```
- Server retrieves OAuth token on startup
- Background task refreshes every 4 minutes (token expires in 5 minutes)
- MCP tools automatically use server token when no manual token provided
- No manual token handling required in Claude Desktop

### MCP 1.21.0 Modern Patterns

- **Lifespan Context**: Uses `@asynccontextmanager` pattern with `ctx.request_context.lifespan_context`
- **Tool Decorators**: `@app.tool()` and `@app.resource()` with metadata annotations
- **Streamable HTTP**: Native HTTP transport without external workarounds
- **Type Safety**: `AppContext` dataclass for dependency injection

### Resource and Tool Patterns

**MCP Resources**: `solr://search/{query}` for simple search interface
**MCP Tools**:
- `search`: Advanced search with filtering, sorting, pagination, faceting, highlighting, and edismax multi-field search
- `get_document`: Document retrieval by ID with field selection
- Both tools support optional `access_token` parameter for OAuth (auto-filled when OAUTH_AUTO_REFRESH=true)

Both implement identical business logic but different protocol interfaces.

### Testing Strategy

**Unit Tests** (`tests/test_server.py`): Mock Solr responses to test logic without external dependencies
**Integration Tests** (`tests/test_integration_server.py`): Real Solr container tests marked with `@pytest.mark.integration`

Integration tests automatically skip when Solr is unavailable, making them safe for CI/CD.

## Important Context7 Usage

Always use Context7 MCP Server for library documentation (start with 5000 tokens, increase to 20000 if needed, limit to 3 attempts per documentation search).

## Project Management

Check `TASK.md` before starting work and update it when completing tasks. Follow the existing modular structure in `src/server/` rather than the legacy monolithic files.