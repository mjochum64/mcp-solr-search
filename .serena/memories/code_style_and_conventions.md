# Code Style and Conventions

## Code Formatting
- **Black**: Line length 88 characters, Python 3.11 target
- **Flake8**: Max line length 88, excludes __pycache__, .git, .venv, .mypy_cache

## Project Structure Conventions
```
/src/
  server/
    mcp_server.py      # Main MCP server implementation
    http_server.py     # FastAPI HTTP server
    solr_client.py     # Solr client class
    models.py          # Pydantic data models
  main.py              # CLI entry point
  server.py            # Legacy server (being phased out)
/tests/
  test_*.py            # Test files with descriptive names
  */                   # Organized test subdirectories
/docker/               # Docker configurations
/.vscode/              # VSCode tasks and launch configs
```

## Naming Conventions
- **Files**: snake_case (e.g., `mcp_server.py`, `solr_client.py`)
- **Classes**: PascalCase (e.g., `SolrClient`, `SearchParams`)
- **Functions/Variables**: snake_case (e.g., `search_solr`, `get_document`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `SOLR_BASE_URL`, `MCP_SERVER_PORT`)

## Documentation Standards
- **Docstrings**: Module-level docstrings for all files
- **Type Hints**: Pydantic models for request/response validation
- **Comments**: German comments in some files, English preferred for new code

## Async/Await Patterns
- All Solr interactions are async using httpx
- MCP server functions are async
- Proper async context management with lifespan handlers

## Error Handling
- Structured error responses using Pydantic models
- Proper HTTP status codes in FastAPI endpoints
- Logging with Python's logging module