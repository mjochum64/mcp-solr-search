# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv (recommended)
uv install

# Or with pip
pip install -e .

# Create and activate virtual environment (always required)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .\.venv\Scripts\activate   # Windows
```

### Running the Solr Environment
```bash
# Start Solr with sample data
./start_solr.sh

# Access Solr Admin UI
# http://localhost:8983/solr/
```

### Running the MCP Server
```bash
# Show available modes
python run_server.py --mode help

# Run MCP protocol server (for LLM integration)
python run_server.py --mode mcp

# Run HTTP API server (for direct testing)
python run_server.py --mode http

# Development with MCP Inspector GUI
mcp dev src/server/mcp_server.py
```

### Testing
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/test_server.py

# Run integration tests (requires running Solr)
pytest tests/test_integration_server.py -m integration

# Run with coverage
pytest --cov=src
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8
```

## Architecture Overview

This is an MCP (Model Context Protocol) server that provides Apache Solr document search capabilities to LLMs. The key architectural components are:

### Core Components
- **MCP Server** (`src/server/mcp_server.py`): Main MCP protocol implementation using FastMCP
- **HTTP Server** (`src/server/http_server.py`): Alternative HTTP API for direct access (MCP 1.6.0 workaround)
- **Solr Client** (`src/server/solr_client.py`): Async HTTP client for Solr communication
- **Models** (`src/server/models.py`): Pydantic models for request/response validation

### MCP 1.6.0 Compatibility Notes
- Uses global variables instead of `app.state` (not supported in MCP 1.6.0)
- Avoids `lifespan` context manager (causes TaskGroup errors)
- HTTP access requires separate FastAPI server (`http_server.py`)

### Dual Server Architecture
The project provides two server modes:
1. **MCP Protocol Mode**: Standard MCP server for LLM integration via `run_server.py --mode mcp`
2. **HTTP API Mode**: Direct HTTP access via `run_server.py --mode http` (port 8765)

### MCP Interface
- **Resource**: `solr://search/{query}` - Basic search functionality
- **Tool**: `search` - Advanced search with filtering, sorting, and pagination
- **Tool**: `get_document` - Retrieve specific documents by ID

### Development Environment
- Uses Docker Compose with Solr 9.4+ container
- Includes sample documents collection named "documents"
- Configuration via `.env` file (copy from `.env.example`)

### Testing Strategy
- Unit tests with mocked Solr responses (`test_server.py`)
- Integration tests with real Solr instance (`test_integration_server.py`)
- MCP Inspector GUI for interactive testing (`mcp dev`)