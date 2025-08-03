# Tech Stack and Dependencies

## Core Technologies
- **Python**: 3.11+ (3.10+ supported)
- **MCP**: Model Context Protocol 1.6.0 (migration to 2025-03-26 planned)
- **Apache Solr**: 9.4+ for document search and indexing
- **Docker**: For Solr development environment

## Key Dependencies
```toml
# Core runtime dependencies
python-dotenv>=1.0.0     # Environment configuration
httpx>=0.24.1           # Async HTTP client for Solr communication
mcp[cli]>=1.6.0         # Model Context Protocol SDK
pydantic>=2.0.0         # Data validation and serialization
pyjwt>=2.6.0           # JWT authentication
passlib>=1.7.4         # Password hashing
fastapi                 # HTTP server (MCP 1.6.0 workaround)
uvicorn                 # ASGI server
```

## Development Dependencies
```toml
# Development and testing
pytest>=7.0            # Testing framework
pytest-asyncio>=0.21.0 # Async testing support
pytest-cov>=4.1.0      # Coverage reporting
black                   # Code formatting
flake8                  # Code linting
```

## Package Manager
- **Primary**: `uv` (recommended, faster dependency resolution)
- **Fallback**: `pip` (standard Python package manager)

## Containerization
- **Docker Compose**: Solr development environment
- **Solr Image**: Apache Solr 9.4 official image
- Sample data loading with custom Python script