# MCP-Server for Apache Solr Document Search

This project implements a Model Context Protocol (MCP) server that provides document search capabilities through Apache Solr. It allows Large Language Models to search and retrieve documents from Solr collections using the MCP standard.

## Features

- MCP Resources for searching Solr documents
- MCP Tools for advanced search and document retrieval
- Asynchronous communication with Solr using httpx
- Type-safe interfaces with Pydantic models
- Authentication support (JWT)
- Comprehensive test suite

## What is MCP?

The [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk) is a standardized way for applications to provide context to Large Language Models (LLMs). This project implements an MCP server that exposes Apache Solr's search capabilities to LLMs, allowing them to:

- Search for documents using simple or complex queries
- Retrieve specific documents by ID
- Filter, sort, and paginate search results

## Requirements

- Python 3.11+
- Apache Solr instance
- `uv` package manager (recommended)

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

## Usage

### Running the MCP Server

You can run the MCP server directly:

```bash
python src/server.py
```

Or use the MCP development tools with the included inspector:

```bash
mcp dev src/server.py
```

For Claude Desktop integration:

```bash
mcp install src/server.py --name "Solr Search"
```

### Using the Solr MCP Server

The server exposes the following MCP endpoints:

- **Resource**: `solr://search/{query}` - Basic search functionality
- **Tool**: `search` - Advanced search with filtering, sorting, and pagination
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

## Development

### Running Tests

```bash
pytest
```

Or with coverage:

```bash
pytest --cov=src
```

### Project Structure

```
/src
  server.py         # Main MCP server implementation
/tests
  test_server.py    # Tests for the MCP server
.env.example        # Environment variables template
pyproject.toml      # Project configuration
PLANNING.md         # Project planning document
TASK.md             # Project tasks and progress tracking
README.md           # This file
```

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
