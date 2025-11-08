# Codebase Structure and Architecture

## Main Directory Structure
```
mcp-solr-search/
├── src/                     # Source code
│   ├── server/             # Modular server components
│   │   ├── mcp_server.py   # MCP protocol server
│   │   ├── http_server.py  # FastAPI HTTP server
│   │   ├── solr_client.py  # Solr communication client
│   │   └── models.py       # Pydantic data models
│   ├── main.py             # CLI entry point with arg parsing
│   ├── server.py           # Legacy monolithic server
│   └── fastapi_server.py   # Legacy FastAPI server
├── tests/                  # Test suite
│   ├── test_server.py      # Unit tests with mocks
│   ├── test_integration_server.py  # Integration tests
│   ├── test_main.py        # CLI tests
│   ├── archived/           # Old test files
│   ├── http/              # HTTP-specific tests
│   └── tools/             # Tool-specific tests
├── docker/                 # Docker configurations
│   └── solr/              # Solr setup and sample data
├── .vscode/               # VSCode tasks and launch configs
└── [config files]         # pyproject.toml, README.md, etc.
```

## Key Components

### 1. MCP Server (`src/server/mcp_server.py`)
- Implements MCP protocol for LLM integration
- Provides resources: `solr://search/{query}`
- Provides tools: `search`, `get_document`
- Uses lifespan management for Solr client

### 2. HTTP Server (`src/server/http_server.py`)
- FastAPI-based server for direct HTTP access
- Mimics MCP interface with HTTP endpoints
- Workaround for MCP 1.6.0 limitations
- Provides `/tool/search`, `/resource/...` endpoints

### 3. Solr Client (`src/server/solr_client.py`)
- Async HTTP client using httpx
- Handles Solr communication and error handling
- Methods: `search()`, `get_document()`, `test_connection()`

### 4. Data Models (`src/server/models.py`)
- Pydantic models for type safety
- `SearchParams`: Search query parameters
- `GetDocumentParams`: Document retrieval parameters
- `ErrorResponse`: Standardized error format

## Entry Points
- **`run_server.py`**: Main convenience script
- **`src/main.py`**: CLI argument parsing and server startup
- **VSCode Tasks**: Predefined development tasks

## MCP 1.6.0 Compatibility Notes
- Global variables used instead of `app.state` (not supported)
- Lifespan manager avoided due to TaskGroup errors
- HTTP server provides alternative access method
- Planned migration to MCP 2025-03-26 will resolve these issues

## Testing Architecture
- **Unit Tests**: Mock Solr responses, test logic
- **Integration Tests**: Real Solr container required
- **Coverage**: pytest-cov for coverage reporting
- **Async Testing**: pytest-asyncio for async test support