# Project Tasks: MCP-Server for Apache Solr (Focus: Document Search)

## Current Status & Version History (Updated: 8. November 2025)

**Current Version**: **1.3.1** ✅
**MCP Version**: **MCP 1.21.0** (2025-06-18 specification) ✅

### Version 1.3.1 - MCP Spec Update (8. November 2025)
- [x] Updated documentation to MCP Specification 2025-06-18 (latest)
- [x] Updated CLAUDE.md, README.md, TASK.md to reference 2025-06-18
- [x] Added comprehensive migration roadmap for future spec compliance
- [x] Documented OAuth 2.1 requirement for production deployment

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
- [x] Upgraded to MCP 1.21.0 with 2025-06-18 specification support
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
- [ ] Implement OAuth 2.1 authorization (mandatory in 2025-06-18 for production)
- [ ] Implement Resource Indicators (RFC 8707) for security
- [ ] Add structured tool outputs with Pydantic schemas
- [ ] Evaluate JSON-RPC batching support
- [ ] Multiple cores/collections support
- [ ] Schema inspection tool
- [ ] Advanced highlighting configuration options

---

## MCP Spec 2025-06-18 Migration Roadmap

### ✅ Current Status (as of 8. November 2025)

**Protocol Version:** 2025-06-18 (latest)
**SDK Version:** MCP 1.21.0
**Compatibility:** ✅ Fully compatible - SDK supports 2024-11-05, 2025-03-26, and 2025-06-18

**Documentation Status:**
- ✅ CLAUDE.md updated to 2025-06-18
- ✅ README.md updated to 2025-06-18
- ✅ TASK.md updated to 2025-06-18
- ✅ CHANGELOG.md updated with v1.3.1 entry

### 📋 Migration Phases

#### Phase 1: Documentation Update (✅ COMPLETED - 8. Nov 2025)
**Estimated Effort:** ~30 minutes
**Status:** ✅ Done

**Tasks:**
- [x] Update CLAUDE.md specification references
- [x] Update README.md specification references
- [x] Update TASK.md with new spec version
- [x] Add CHANGELOG.md entry for v1.3.1
- [x] Update "Next Steps" with new mandatory features

**Result:** All documentation now references 2025-06-18 specification.

---

#### Phase 2: OAuth 2.1 Authorization Implementation (❌ PENDING)
**Estimated Effort:** 8-16 hours
**Priority:** 🔴 High (mandatory for production deployment)
**Required for:** Production-ready public server

**Background:**
- 2025-03-26: OAuth was optional
- 2025-06-18: OAuth 2.1 is **mandatory** for production
- Current status: Local development server without auth

**Tasks:**

##### 2.1 OAuth Infrastructure Setup (~4 hours)
- [ ] Configure OAuth 2.1 provider (choose: Auth0, Keycloak, or custom)
- [ ] Set up OAuth endpoints in environment
- [ ] Implement OAuth2Config in mcp_server.py
- [ ] Add OAuth environment variables to .env.example
- [ ] Document OAuth setup process in README.md

**Example Implementation:**
```python
# src/server/mcp_server.py
from mcp.client.auth.oauth2 import OAuth2Config

# OAuth Configuration (only for production)
if os.getenv("ENABLE_OAUTH", "false").lower() == "true":
    oauth_config = OAuth2Config(
        authorization_endpoint=os.getenv("OAUTH_AUTH_ENDPOINT"),
        token_endpoint=os.getenv("OAUTH_TOKEN_ENDPOINT"),
        client_id=os.getenv("OAUTH_CLIENT_ID"),
        client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
        scopes=["solr:read", "solr:search"]
    )
```

##### 2.2 Authorization Middleware (~3 hours)
- [ ] Implement authorization checks in tool functions
- [ ] Add token validation middleware
- [ ] Implement permission-based access control
- [ ] Add authorization error handling

**Example Implementation:**
```python
@app.tool()
async def search(query: str, ctx: Context = None) -> Dict[str, Any]:
    # Authorization check
    if not await is_authorized(ctx, "solr:search"):
        return {"error": "Unauthorized: Missing solr:search permission"}

    # Existing search logic...
```

##### 2.3 Testing (~2 hours)
- [ ] Create OAuth mock for unit tests
- [ ] Add authorization unit tests
- [ ] Test unauthorized access scenarios
- [ ] Integration tests with OAuth flow
- [ ] Security tests for token validation

##### 2.4 Documentation (~1 hour)
- [ ] OAuth setup guide in README.md
- [ ] Environment variables documentation
- [ ] Security best practices
- [ ] Troubleshooting guide

**Dependencies:**
- OAuth provider (Auth0, Keycloak, etc.)
- SSL/TLS certificates for production
- Updated environment configuration

**Deliverables:**
- OAuth 2.1 authentication flow
- Token-based authorization
- Documented setup process
- Comprehensive tests

---

#### Phase 3: Resource Indicators (RFC 8707) (~2-3 hours)
**Estimated Effort:** 2-3 hours
**Priority:** 🟡 Medium (security enhancement)
**Required for:** Preventing token theft by malicious servers

**Background:**
- RFC 8707: OAuth 2.0 Resource Indicators
- Prevents malicious MCP servers from obtaining access tokens
- MCP Clients must implement this when our server acts as client

**Tasks:**

##### 3.1 Implementation (~2 hours)
- [ ] Implement Resource Indicators in OAuth flow
- [ ] Add resource parameter to token requests
- [ ] Validate resource indicators in token responses
- [ ] Update OAuth configuration

##### 3.2 Testing & Documentation (~1 hour)
- [ ] Unit tests for Resource Indicators
- [ ] Security tests for token scope validation
- [ ] Document Resource Indicators usage

**Note:** Only relevant if we act as MCP Client to other servers.

---

#### Phase 4: Structured Tool Outputs (~4-6 hours)
**Estimated Effort:** 4-6 hours
**Priority:** 🟢 Low (quality improvement, not mandatory)
**Required for:** Better type safety and API clarity

**Background:**
- 2025-06-18 introduces structured tool outputs
- Tools can define response schemas with Pydantic
- Better validation and documentation

**Tasks:**

##### 4.1 Response Models (~2 hours)
- [ ] Create Pydantic models for search responses
- [ ] Create model for get_document responses
- [ ] Add response models to models.py
- [ ] Add validation and examples

**Example Implementation:**
```python
# src/server/models.py
from pydantic import BaseModel, Field

class SearchResponse(BaseModel):
    """Structured response for search tool."""
    responseHeader: Dict[str, Any] = Field(..., description="Solr response header")
    response: Dict[str, Any] = Field(..., description="Search results")
    facet_counts: Optional[Dict[str, Any]] = Field(None, description="Facet aggregations")
    highlighting: Optional[Dict[str, Any]] = Field(None, description="Highlighted snippets")

    class Config:
        schema_extra = {
            "example": {
                "responseHeader": {"status": 0, "QTime": 5},
                "response": {"numFound": 10, "docs": [...]},
                "highlighting": {"doc1": {"title": ["<em>Python</em>"]}}
            }
        }
```

##### 4.2 Tool Updates (~1 hour)
- [ ] Update search tool with structured output
- [ ] Update get_document tool with structured output
- [ ] Add output schemas to tool annotations

##### 4.3 Testing (~1 hour)
- [ ] Update unit tests for structured outputs
- [ ] Validation tests for response schemas
- [ ] Integration tests

##### 4.4 Documentation (~1 hour)
- [ ] Document response schemas
- [ ] Update API examples
- [ ] Add schema to tool descriptions

**Deliverables:**
- Type-safe tool responses
- Self-documenting API
- Better error detection

---

#### Phase 5: JSON-RPC Batching Support (~3-4 hours)
**Estimated Effort:** 3-4 hours
**Priority:** 🟢 Low (performance optimization)
**Required for:** High-performance scenarios with multiple requests

**Background:**
- 2025-06-18 adds support for JSON-RPC batching
- Multiple requests can be sent in single HTTP call
- Reduces network overhead

**Tasks:**

##### 5.1 Implementation (~2 hours)
- [ ] Enable batch request handling
- [ ] Implement parallel processing of batched requests
- [ ] Add batch response formatting

##### 5.2 Testing (~1 hour)
- [ ] Unit tests for batch requests
- [ ] Performance tests
- [ ] Error handling tests

##### 5.3 Documentation (~1 hour)
- [ ] Batch request examples
- [ ] Performance guidelines

---

### 📊 Migration Timeline

| Phase | Priority | Effort | Status | Target Date |
|-------|----------|--------|--------|-------------|
| Phase 1: Documentation | ✅ Mandatory | 0.5h | ✅ Done | Nov 8, 2025 |
| Phase 2: OAuth 2.1 | 🔴 High | 8-16h | ❌ Pending | TBD (before production) |
| Phase 3: Resource Indicators | 🟡 Medium | 2-3h | ❌ Pending | TBD (with OAuth) |
| Phase 4: Structured Outputs | 🟢 Low | 4-6h | ❌ Pending | TBD (optional) |
| Phase 5: JSON-RPC Batching | 🟢 Low | 3-4h | ❌ Pending | TBD (optional) |

**Total Effort:** 17.5 - 33.5 hours (excluding optional phases)

---

### 🎯 Recommendations

#### For Local Development / Testing:
✅ **Current setup is sufficient!**
- 2025-06-18 spec is fully supported by SDK
- OAuth not required for local usage
- No breaking changes needed

#### For Production Deployment:
🔴 **Phase 2 (OAuth 2.1) is MANDATORY**
- Required by 2025-06-18 specification
- Must be implemented before public deployment
- Recommended timeline: 2-3 weeks before go-live

#### Optional Enhancements:
🟢 **Phase 4 (Structured Outputs)**
- Recommended for API quality
- Can be done incrementally
- Good for long-term maintainability

🟢 **Phase 3 & 5**
- Only if specific security/performance needs
- Can be deferred

---

### 📚 Additional Resources

**MCP Specification:**
- Latest Spec: https://modelcontextprotocol.io/specification/2025-06-18
- OAuth Guide: https://modelcontextprotocol.io/specification/2025-06-18/authorization
- RFC 8707: https://datatracker.ietf.org/doc/html/rfc8707

**SDK Documentation:**
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- OAuth Examples: See SDK examples/oauth

**OAuth Providers:**
- Auth0: https://auth0.com/
- Keycloak: https://www.keycloak.org/
- Okta: https://www.okta.com/

---

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
