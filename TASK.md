# Project Tasks: MCP-Server for Apache Solr (Focus: Document Search)

## Current Status & Version History (Updated: 8. November 2025)

**Current Version**: **1.3.0** ✅
**MCP Version**: **MCP 1.21.0** (2025-03-26 specification) ✅

### Version 1.3.0 - Highlighting Support (8. November 2025)
- [x] Implemented Highlighting to show where search terms appear
- [x] Added `highlight_fields` parameter to search tool
- [x] Highlighting with `<em>` tags around matched terms
- [x] Unit tests and integration tests with live Solr
- [x] Documentation and examples updated

### Version 1.2.0 - Faceted Search Support (8. November 2025)
- [x] Implemented Faceted Search for data exploration
- [x] Added `facet_fields` parameter to search tool
- [x] Automatic aggregation of field values with counts
- [x] Unit tests and integration tests with live Solr
- [x] Documentation and examples updated

### Version 1.1.0 - MCP 1.21.0 Modernization (8. November 2025)
- [x] Upgraded to MCP 1.21.0 with 2025-03-26 specification support
- [x] Removed MCP 1.6.0 compatibility workarounds:
  - [x] Replaced global variables with proper lifespan context pattern
  - [x] Implemented modern lifespan context manager with AppContext dataclass
  - [x] Added Streamable HTTP transport support (native in MCP 1.21.0)
- [x] Implemented new MCP features:
  - [x] Tool Annotations (readOnlyHint) for better client integration
  - [x] Modern FastMCP decorator pattern (@app.tool, @app.resource)
  - [x] Context-based state management (ctx.request_context.lifespan_context)
  - [x] Enhanced logging with ctx.info/debug/warning/error
- [x] Updated all unit tests for new patterns
- [x] Verified Streamable HTTP transport functionality
- [x] Updated README.md with new MCP version and features
- [x] Updated CLAUDE.md with modern patterns
- [x] Tested Claude Desktop integration with MCP 1.21.0

### Next Steps (Priority Order)
- [ ] Consider implementing OAuth 2.1 authorization (new in 2025-03-26)
- [ ] Evaluate JSON-RPC batching support
- [ ] Multiple cores/collections support
- [ ] Schema inspection tool
- [ ] Advanced highlighting configuration options

## 1. Project Setup (Completed: 26. April 2025)

- [x] Create `pyproject.toml` with necessary dependencies (MCP SDK, Pydantic, httpx, etc.)
- [x] Set up `.env.example` template with Solr connection and authentication variables
- [x] Establish project folder structure:

  ```plaintext
  /src
    server.py         # Main MCP server implementation
  /tests
    test_server.py    # Tests for the MCP server
  .env.example
  README.md
  PLANNING.md
  ```

- [ ] Initialize Git repository and create initial commit

## 2. MCP Server Development

- [x] Set up basic MCP server in `src/server.py`
- [x] Configure MCP server with lifespan management
- [x] Implement resource and tool structure for Solr integration
- [x] Create Pydantic models for request/response validation
- [ ] Add context management for user sessions (if needed)
- [x] Write unit tests for MCP server resources and tools

## 3. Apache Solr Integration

- [x] Implement Solr client class in server.py
- [x] Configure httpx for asynchronous Solr requests
- [x] Create search functionality as MCP resources and tools
- [x] Implement support for:
  - [x] Basic search functionality
  - [x] Faceted search (v1.2.0)
  - [x] Highlighting (v1.3.0)
  - [ ] Multiple cores/collections
  - [x] Document retrieval by ID
- [x] Add error handling for Solr connection and query issues
- [x] Write unit tests for Solr client functions
- [x] Set up Docker-based test environment for Apache Solr

## 4. Authentication System (if needed)

- [ ] Create user management functionality
- [ ] Implement JWT-based authentication with pyjwt
- [ ] Set up secure password hashing with passlib
- [ ] Build login function
- [ ] Implement token issuance, validation, and renewal functions
- [ ] Create authentication context for MCP tools and resources
- [ ] Configure optional role-based access control
- [ ] Write unit tests for authentication functionality

## 5. MCP Resources and Tools Enhancement

- [x] Implement search resource (`solr://search/{query}`):
  - [x] Simple interface for basic searches
  - [x] Error handling
- [x] Create search tool with advanced parameters:
  - [x] Query parameter validation
  - [x] Support for filter queries, sorting, and pagination
  - [x] Support for facets (v1.2.0)
  - [x] Support for highlighting (v1.3.0)
- [x] Implement document retrieval tool:
  - [x] Support for retrieving by ID
  - [x] Support for field selection
  - [ ] Support for document transformation and formatting
- [ ] Add additional helper tools:
  - [ ] Collection/core management
  - [ ] Schema inspection
  - [ ] Statistics gathering
- [x] Write comprehensive tests:
  - [x] Expected behavior tests
  - [x] Edge case tests
  - [x] Failure scenario tests with real Solr integration

## 6. Error Handling and Logging

- [x] Implement basic error handling
- [ ] Create standardized error response models
- [ ] Configure logging system for requests and special events
- [ ] Add Solr error translation to readable user messages
- [ ] Implement request tracking and debugging tools
- [x] Write tests for error handling scenarios

## 7. MCP Client Example (Optional)

- [ ] Create example MCP client to demonstrate usage
- [ ] Implement basic CLI for interacting with the MCP server
- [ ] Show how to integrate with LLM applications

## 8. Deployment Preparation

- [x] Set up MCP CLI installation configuration
- [ ] Create Dockerfile for containerization
- [x] Set up Docker Compose configuration for development and testing
- [x] Document deployment process in README.md
- [x] Implement environment variable configuration
- [x] Add health check capabilities
- [x] Test deployment in containerized environment
- [ ] Test Claude Desktop integration
- [x] Test MCP development tools (mcp dev) (26. April 2025)
- [x] VSCode Integration mit Launch-Konfigurationen und Tasks (26. April 2025)

## 9. Documentation

- [x] Update README.md with:
  - [x] Project overview
  - [x] Setup instructions
  - [x] Usage examples
  - [x] MCP resources and tools documentation
- [x] Document environment variables in .env.example
- [x] Create and set up CHANGELOG.md for tracking project changes
- [ ] Add inline code documentation for all modules and functions
- [ ] Create example usage scripts

## Legacy Issues (MCP 1.6.0) - To be resolved in modernization

### Completed Workarounds (MCP 1.6.0)
- [x] Fix MCP 1.6.0 Server TaskGroup error - Using a bare server without lifespan manager resolves the issue (26. April 2025)
- [x] MCP 1.6.0 doesn't support app.state - Must use global variables instead of app.state to store shared resources (26. April 2025)
- [x] MCP 1.6.0 doesn't support direct HTTP access - The FastMCP.run() method only supports 'stdio' or 'sse' transport, not HTTP (26. April 2025)
- [x] Created FastAPI-based workaround for direct HTTP access - Implemented a FastAPI server that mimics MCP functionality but ensures HTTP accessibility (26. April 2025)
- [x] Reorganize code into modular structure with separate components for Solr client, models, MCP server, and HTTP server (26. April 2025)
- [x] Create centralized entry point (main.py) with command-line arguments for different server modes (26. April 2025)
- [x] VSCode-Konfiguration mit launch.json und tasks.json für einfaches Debugging und Ausführen (26. April 2025)
- [x] VS Code-Tasks angepasst, um virtuelle Umgebung zu aktivieren (27. April 2025)

### Integration Issues (To be tested with new MCP version)
- [ ] Claude Desktop App kann den MCP-Server nicht starten - "spawn uv ENOENT" Fehler (27. April 2025)
- [ ] Alternative Installation des MCP-Servers für Claude ohne uv-Abhängigkeit (27. April 2025)
- [ ] HTTP-Server als Alternative für Claude Desktop App-Integration testen (27. April 2025)

## Future Enhancements

- [ ] Investigate how to implement MCP server authentication best practices
- [ ] Explore creating a prompts interface for common Solr search templates
- [ ] Consider implementing MCP contexts for more complex operations
- [ ] Research MCP server monitoring and analytics capabilities
- [ ] Consider implementing schema detection for auto-configuring search fields
- [ ] Explore adding facet support for improved document exploration
- [ ] Alternative Integrationsmöglichkeit für GitHub Copilot Chat finden
