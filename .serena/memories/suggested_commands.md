# Suggested Commands for Development

## Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .\.venv\Scripts\activate  # Windows

# Install dependencies
uv install                 # Preferred
# OR
pip install -e .          # Alternative with pip
```

## Development Servers
```bash
# Start MCP server (for LLM integration)
python run_server.py --mode mcp

# Start HTTP server (for direct HTTP access)
python run_server.py --mode http

# Start MCP development server with inspector GUI
mcp dev src/server/mcp_server.py

# Show available options
python run_server.py --mode help
```

## Solr Development Environment
```bash
# Start Solr container with sample data
./start_solr.sh

# Stop Solr container
docker compose down

# View Solr logs
docker compose logs solr

# Access Solr Admin UI
# http://localhost:8983/solr/
```

## Testing Commands
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/test_server.py

# Run integration tests (requires running Solr)
pytest tests/test_integration_server.py -m integration

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_server.py::test_search_solr_resource -v
```

## Code Quality
```bash
# Format code with Black
black src/ tests/

# Lint with Flake8
flake8 src/ tests/

# Run both formatting and linting
black src/ tests/ && flake8 src/ tests/
```

## Git Commands
```bash
# Standard git workflow
git status
git add .
git commit -m "Description"
git push origin mcp-modernization-2025

# View recent commits
git log --oneline -10
```

## System Commands (Linux)
```bash
# Basic file operations
ls -la                    # List files with details
find . -name "*.py"      # Find Python files
grep -r "search" src/    # Search for text in files

# Process management
ps aux | grep python     # Find Python processes
kill -9 <pid>           # Kill process by PID

# Network
netstat -tlnp | grep 8765  # Check if port is in use
curl http://localhost:8765/  # Test HTTP endpoint
```