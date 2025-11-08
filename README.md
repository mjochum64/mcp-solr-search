# MCP-Server for Apache Solr Document Search

This project implements a Model Context Protocol (MCP) server that provides document search capabilities through Apache Solr. It allows Large Language Models to search and retrieve documents from Solr collections using the MCP standard.

## Features

- MCP Resources for searching Solr documents
- MCP Tools for advanced search and document retrieval
- **Faceted Search** support for data exploration and aggregation
- **Highlighting** support to show where search terms appear in results
- Asynchronous communication with Solr using httpx
- Type-safe interfaces with Pydantic models
- Authentication support (JWT)
- Comprehensive test suite
- Docker-based Solr development environment

## Current Version

**Version 1.3.0** - Added Highlighting support to show where search terms appear in results. See [CHANGELOG.md](CHANGELOG.md) for details on all changes.

## What is MCP?

The [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk) is a standardized way for applications to provide context to Large Language Models (LLMs). This project implements an MCP server that exposes Apache Solr's search capabilities to LLMs, allowing them to:

- Search for documents using simple or complex queries
- Retrieve specific documents by ID
- Filter, sort, and paginate search results

## Requirements

- Python 3.11+
- Docker and Docker Compose (for the integrated Solr environment)
- `uv` package manager (recommended)
- MCP 1.21.0+ (fully compatible with 2025-03-26 specification)

## Installation

1. Install `uv` (if not already installed):

   ```bash
   pip install uv
   ```

2. Install the project dependencies:

   ```bash
   uv install
   ```

   Or with pip:

   ```bash
   pip install -e .
   ```

3. Copy the environment template and configure it:

   ```bash
   cp .env.example .env
   # Edit .env with your Solr connection details
   ```

4. Create and activate a virtual environment (important):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Linux/macOS
   # OR
   .\.venv\Scripts\activate   # On Windows
   ```

   > **Note**: Always ensure the virtual environment is activated before running the server or client tools. Many connection issues are caused by running commands outside the virtual environment.

## MCP 1.21.0 Modern Features

This project uses the latest MCP 1.21.0 SDK with full support for the 2025-03-26 specification:

✅ **Lifespan Context Manager**: Type-safe dependency injection with `AppContext` dataclass
✅ **Streamable HTTP Transport**: Native HTTP support without external workarounds
✅ **Tool Annotations**: Enhanced metadata (`readOnlyHint`, `title`, `description`)
✅ **Context-Based Logging**: Direct client communication via `ctx.info/debug/warning/error`
✅ **Modern Decorators**: `@app.tool()` and `@app.resource()` patterns

### Migration from MCP 1.6.0

The project has been fully modernized from MCP 1.6.0. Key changes:
- ❌ Global variables → ✅ Lifespan context (`ctx.request_context.lifespan_context`)
- ❌ TaskGroup errors → ✅ Stable `@asynccontextmanager` pattern
- ❌ FastAPI HTTP workaround → ✅ Native Streamable HTTP transport

## Native HTTP Support (Streamable HTTP)

MCP 1.21.0 includes native **Streamable HTTP transport** support. Start the server with HTTP transport:

```bash
# Run with native Streamable HTTP transport
python src/server/mcp_server.py --http
# Or use the convenience wrapper
python run_server.py --mode http
```

The server will be available at `http://127.0.0.1:8000` with full MCP protocol support over HTTP.

### Legacy HTTP Server

The FastAPI-based HTTP server (`src/server/http_server.py`) is still available for backwards compatibility:

```bash
python run_server.py --mode http-legacy
```

**Note**: The legacy HTTP server is no longer required with MCP 1.21.0 and may be deprecated in future versions. Use native Streamable HTTP transport for new integrations.

## Usage

### Starting the Solr Development Environment

The project includes a Docker Compose setup with Apache Solr and sample documents for development and testing:

```bash
# Start the Solr container with sample data
./start_solr.sh

# Access the Solr Admin UI
open http://localhost:8983/solr/
```

This will:
1. Start an Apache Solr 9.4 container
2. Create a "documents" collection
3. Load 10 sample documents with various fields
4. Configure everything for immediate use with the MCP server

### Running the MCP Server

You can run the MCP server using the provided wrapper script which supports different modes:

```bash
# Show help and available options
python run_server.py --mode help

# Run the MCP protocol server (for LLM integration)
python run_server.py --mode mcp

# Run the HTTP API server (for direct HTTP access)
python run_server.py --mode http

# Specify a custom port
python run_server.py --mode http --port 9000
```

For development with MCP Inspector GUI:

```bash
# MCP development environment with inspector GUI
mcp dev src/server/mcp_server.py
```

For Claude Desktop integration:

```bash
# Install the MCP server for Claude Desktop
mcp install src/server/mcp_server.py --name "Solr Search"
```

### Using the Solr MCP Server

The server exposes the following MCP endpoints:

- **Resource**: `solr://search/{query}` - Basic search functionality
- **Tool**: `search` - Advanced search with filtering, sorting, pagination, faceting, and highlighting
- **Tool**: `get_document` - Retrieve specific documents by ID

### Example: Using the search tool

```python
# Example of using the search tool from an MCP client
result = await session.call_tool(
    "search",
    arguments={
        "query": "machine learning",
        "filter_query": "category:technology",
        "sort": "date desc",
        "rows": 5,
        "start": 0
    }
)
```

### Example: Using faceted search

```python
# Example of using faceted search to explore data
result = await session.call_tool(
    "search",
    arguments={
        "query": "*:*",
        "rows": 10,
        "facet_fields": ["category", "author"]
    }
)
# Response includes facet_counts with aggregated counts per field value
# e.g., {"category": ["programming", 3, "technology", 3, ...]}
```

### Example: Using highlighting

```python
# Example of using highlighting to show where search terms appear
result = await session.call_tool(
    "search",
    arguments={
        "query": "title:machine",
        "rows": 10,
        "highlight_fields": ["title", "content"]
    }
)
# Response includes highlighting with <em> tags around matched terms
# e.g., {"doc2": {"title": ["<em>Machine</em> Learning Basics"], ...}}
```

### Example: Using the document retrieval tool

```python
# Example of retrieving a document by ID
document = await session.call_tool(
    "get_document",
    arguments={
        "id": "doc123",
        "fields": ["title", "content", "author"]
    }
)
```

## Configuration

The following environment variables can be configured in your `.env` file:

```
# MCP Server Configuration
MCP_SERVER_NAME=Solr Search
MCP_SERVER_PORT=8765

# Apache Solr Configuration
SOLR_BASE_URL=http://localhost:8983/solr
SOLR_COLLECTION=documents
SOLR_USERNAME=
SOLR_PASSWORD=

# Authentication (for future use)
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440  # 24 hours

# Logging
LOG_LEVEL=INFO
```

## Testing the MCP Server

There are several ways to test and interact with the MCP Solr server:

### 1. Using the MCP Inspector (GUI)

This is the most convenient method for testing and debugging:

```bash
# Start the server with the inspector
mcp dev src/server/mcp_server.py
```

Then open http://127.0.0.1:6274 in your browser to access the MCP Inspector.

#### Executing a search:

1. **Using the Resource**:
   - Find the resource `solr://search/{query}` in the sidebar
   - Replace `{query}` with your search term (e.g., `*:*` for all documents)
   - Click "Execute"

2. **Using the Search Tool**:
   - Go to the "Tools" section and select the "search" tool
   - Enter parameters in JSON format:
   ```json
   {
     "query": "*:*",
     "filter_query": "category:technology",
     "sort": "id asc",
     "rows": 5,
     "start": 0
   }
   ```
   - Click "Execute"

3. **Using Faceted Search**:
   - Go to the "Tools" section and select the "search" tool
   - Enter parameters with facet_fields:
   ```json
   {
     "query": "*:*",
     "rows": 10,
     "facet_fields": ["category", "author"]
   }
   ```
   - Click "Execute"
   - Response will include `facet_counts` with aggregated data per field

4. **Using Highlighting**:
   - Go to the "Tools" section and select the "search" tool
   - Enter parameters with highlight_fields:
   ```json
   {
     "query": "title:machine",
     "rows": 10,
     "highlight_fields": ["title", "content"]
   }
   ```
   - Click "Execute"
   - Response will include `highlighting` with `<em>` tags around matched terms

#### Retrieving a document:

1. Go to the "Tools" section and select the "get_document" tool
2. Enter parameters in JSON format:
   ```json
   {
     "id": "doc1",
     "fields": ["title", "content", "author"]
   }
   ```
3. Click "Execute"

### 2. Using a Python Client

You can create a simple Python client to test the server:

```python
import asyncio
from mcp.client import MCPClient

async def test_solr_search():
    # Connect to the MCP server
    async with MCPClient(url="http://localhost:8765") as client:
        # Get server info to verify connection
        server_info = await client.get_server_info()
        print("Connected to MCP server:", server_info.name)
        
        # Execute a search
        search_result = await client.call_tool(
            "search", 
            arguments={
                "query": "*:*",
                "filter_query": None,
                "sort": "id asc",
                "rows": 5,
                "start": 0
            }
        )
        print("Search results:", search_result)
        
        # If documents were found, retrieve the first one
        if "response" in search_result and search_result["response"]["numFound"] > 0:
            doc_id = search_result["response"]["docs"][0]["id"]
            document = await client.call_tool(
                "get_document",
                arguments={
                    "id": doc_id,
                    "fields": ["title", "content"]
                }
            )
            print(f"Document with ID {doc_id}:", document)

if __name__ == "__main__":
    asyncio.run(test_solr_search())
```

Save this as `test_solr_client.py` and run:
```bash
python test_solr_client.py
```

### 3. Using Direct HTTP Requests

You can also test with curl or any HTTP client. Note that the MCP server expects specific request formats:

```bash
# Testing search tool with curl
curl -X POST http://localhost:8765/tool/search \
  -H "Content-Type: application/json" \
  -d '{"query": "*:*", "rows": 5}'

# Retrieving a document with curl
curl -X POST http://localhost:8765/tool/get_document \
  -H "Content-Type: application/json" \
  -d '{"id": "doc1"}'

# Using the resource endpoint
curl -G http://localhost:8765/resource/solr%3A%2F%2Fsearch%2F%2A%3A%2A \
  --data-urlencode "query=*:*"
```

### 4. Troubleshooting Connection Issues

If you can access the MCP Inspector but not connect with other clients:

1. **Check CORS settings**:
   - If using a web client from a different origin, CORS might be blocking requests

2. **Verify network access**:
   - Ensure port 8765 is accessible from the client

3. **Check for authentication requirements**:
   - If authentication is enabled, ensure clients are including the required credentials

4. **Inspect request format**:
   - MCP expects specific endpoint formats and JSON structures

5. **Use the debug server mode**:
   ```bash
   MCP_DEBUG=1 python run_server.py --mode mcp
   ```

## Integration in Tool-Launcher oder Service-Definitionen

Um den MCP-Server in externe Tools (z.B. Claude Desktop, VSCode Dev Containers, eigene Tool-Runner) einzubinden, verwende folgende Konfiguration:

```json
"solr-search": {
  "command": "/home/mjochum/miniconda3/bin/uv",
  "args": [
    "run",
    "--project",
    "/home/mjochum/projekte/mcp-solr-search",
    "--with",
    "mcp[cli]>=1.21.0",
    "mcp",
    "run",
    "/home/mjochum/projekte/mcp-solr-search/src/server/mcp_server.py"
  ]
}
```

**Wichtig:**
- Verwende **absolute Pfade** für sowohl das `uv` Kommando als auch die Serverdatei
- Passe die Pfade an dein System an (`/home/mjochum/...` → dein Home-Verzeichnis)
- Das `--project` Argument stellt sicher, dass die richtigen Dependencies geladen werden
- Das Kommando sorgt dafür, dass alle Abhängigkeiten (inkl. MCP 1.21.0) im Kontext verfügbar sind

## Development

### Running Tests

```bash
# Run all tests (unit and integration)
pytest

# Run only unit tests
pytest tests/test_server.py

# Run only integration tests (requires running Solr)
pytest tests/test_integration_server.py -m integration

# Run with coverage
pytest --cov=src
```

Integration tests will automatically skip if the Solr server is not available, so they're safe to run even without a running Docker environment.

### Project Structure

```
/src
  server.py         # Main MCP server implementation
/tests
  test_server.py    # Unit tests with mocked Solr responses
  test_integration_server.py # Integration tests with real Solr
/docker
  /solr
    load_sample_data.py  # Script to load sample documents
    /configsets
      /documents
        /conf
          schema.xml     # Solr schema definition
          solrconfig.xml # Solr configuration
          stopwords.txt  # Stopwords for text analysis
docker-compose.yml   # Docker Compose configuration for Solr
start_solr.sh        # Script to start Solr and load data
.env.example         # Environment variables template
pyproject.toml       # Project configuration
PLANNING.md          # Project planning document
TASK.md              # Project tasks and progress tracking
CHANGELOG.md         # Documentation of project changes
README.md            # This file
```

## Versioning

This project follows [Semantic Versioning](https://semver.org/). For the versions available, see the [CHANGELOG.md](CHANGELOG.md) file for details on what has changed in each version.

## Related Resources

- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [Apache Solr Documentation](https://solr.apache.org/guide/)
- [Claude Desktop](https://claude.ai/desktop) - For direct integration with the MCP server

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License.
