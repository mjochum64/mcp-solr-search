# Task Completion Checklist

## When a coding task is completed, always run these commands:

### 1. Code Quality Checks
```bash
# Format code with Black
black src/ tests/

# Lint with Flake8  
flake8 src/ tests/
```

### 2. Testing
```bash
# Run all tests
pytest

# Run with coverage if significant changes
pytest --cov=src
```

### 3. Integration Testing (if Solr-related changes)
```bash
# Start Solr if not running
./start_solr.sh

# Run integration tests
pytest tests/test_integration_server.py -m integration
```

### 4. Manual Testing (for server changes)
```bash
# Test MCP server startup
python run_server.py --mode mcp

# Test HTTP server startup  
python run_server.py --mode http

# Test MCP inspector (for MCP server changes)
mcp dev src/server/mcp_server.py
```

### 5. Environment Verification
```bash
# Ensure virtual environment is active
which python  # Should point to .venv/bin/python

# Verify dependencies are current
uv install    # or pip install -e .
```

## Common Issues to Check
- All tests pass without warnings
- No flake8 linting errors
- Black formatting applied consistently
- Virtual environment is activated
- Solr container is running for integration tests
- No broken imports or missing dependencies

## Pre-commit Verification
Before committing changes:
1. All quality checks pass
2. Tests pass (unit + integration if applicable)
3. Manual smoke test of affected functionality
4. Documentation updated if public API changed