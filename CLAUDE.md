# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) Server for Apache Solr Document Search that bridges LLMs with Solr search capabilities. The project implements both MCP protocol support and HTTP server workarounds due to MCP 1.6.0 limitations, with plans to modernize to MCP 2025-03-26.

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

### Dual Server Architecture
The project implements two parallel server architectures:

1. **MCP Server** (`src/server/mcp_server.py`): Standards-compliant MCP protocol server for LLM integration
2. **HTTP Server** (`src/server/http_server.py`): FastAPI-based server providing HTTP access to MCP functionality

Both servers share the same core components but expose different interfaces due to MCP 1.6.0 limitations.

### Core Components

**SolrClient** (`src/server/solr_client.py`): Async HTTP client managing all Solr communication with error handling and connection management.

**Data Models** (`src/server/models.py`): Pydantic models providing type safety for search parameters, document retrieval, and error responses.

**Entry Point** (`src/main.py`): CLI argument parsing that routes to appropriate server mode, with `run_server.py` as convenience wrapper.

### MCP 1.6.0 Compatibility Workarounds

- **Global Variables**: Uses global `solr_client` instead of `app.state` (not supported in MCP 1.6.0)
- **No Lifespan Manager**: Avoids lifespan context manager due to TaskGroup errors
- **HTTP Fallback**: FastAPI server provides direct HTTP access when MCP transport fails

### Resource and Tool Patterns

**MCP Resources**: `solr://search/{query}` for simple search interface
**MCP Tools**: 
- `search`: Advanced search with filtering, sorting, pagination
- `get_document`: Document retrieval by ID with field selection

Both implement identical business logic but different protocol interfaces.

### Testing Strategy

**Unit Tests** (`tests/test_server.py`): Mock Solr responses to test logic without external dependencies
**Integration Tests** (`tests/test_integration_server.py`): Real Solr container tests marked with `@pytest.mark.integration`

Integration tests automatically skip when Solr is unavailable, making them safe for CI/CD.

## Important Context7 Usage

Always use Context7 MCP Server for library documentation (start with 5000 tokens, increase to 20000 if needed, limit to 3 attempts per documentation search).

## Project Management

Check `TASK.md` before starting work and update it when completing tasks. Follow the existing modular structure in `src/server/` rather than the legacy monolithic files.