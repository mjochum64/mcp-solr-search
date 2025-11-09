# Changelog

This document tracks all significant changes to the MCP Server for Apache Solr.

## [1.4.0] - 2025-11-09

### Added
- **OAuth 2.1 Authorization**: Full implementation with Keycloak integration
  - OAuth2Config dataclass for configuration management
  - TokenValidator class with JWKS and introspection support
  - JWKS caching (1 hour) for performance optimization
  - Fine-grained scope checking (solr:search, solr:read, solr:write, solr:admin)
  - Custom exception classes (TokenMissingError, TokenInvalidError, InsufficientScopesError)
- **Keycloak Integration**:
  - Docker Compose configuration for Keycloak + PostgreSQL
  - Automated setup script (setup-keycloak.sh) for realm/client/scope configuration
  - Automated OAuth flow testing script (test-keycloak.sh)
- **MCP Tools Enhancement**:
  - Extended `search` tool with `access_token` parameter
  - Extended `get_document` tool with `access_token` parameter
  - OAuth validation middleware with clear error messages
- **Comprehensive Testing**:
  - 14 new OAuth unit tests (test_oauth.py) - all passing ✅
  - 10 new integration tests with live Keycloak (test_oauth_integration.py) - all passing ✅
  - Total: 36 tests passing (26 unit + 10 integration)
- **Documentation**:
  - Complete OAuth 2.1 implementation guide (docs/OAUTH_GUIDE.md - 541 lines)
  - Step-by-step Keycloak setup guide (docs/KEYCLOAK_SETUP_GUIDE.md - 404 lines)
  - Comprehensive troubleshooting guide (docs/OAUTH_TROUBLESHOOTING.md - 465 lines)
  - OAuth usage examples in README.md

### Changed
- MCP server AppContext now includes oauth_config and token_validator
- Lifespan manager initializes OAuth components on startup
- .env.example extended with OAuth 2.1 configuration variables
- README.md updated with OAuth implementation status and usage examples
- TASK.md updated with Phase 2 completion status

### Technical Details
- OAuth Provider: Keycloak 23.0
- Token Validation: Both JWKS (fast) and introspection (authoritative) methods
- Security: Complies with MCP Spec 2025-06-18 OAuth 2.1 requirements
- Backward Compatible: OAuth can be disabled for local development (ENABLE_OAUTH=false)
- Production Ready: Full OAuth 2.1 implementation for secure production deployment

## [1.3.1] - 2025-11-08

### Changed
- **MCP Specification Update**: Documentation updated to MCP Spec 2025-06-18 (latest version)
- Updated CLAUDE.md, README.md, TASK.md to reference 2025-06-18 spec
- Extended "Next Steps" with OAuth 2.1 and Resource Indicators (now mandatory for production)

### Technical Details
- MCP SDK 1.21.0 already fully supports 2025-06-18 spec ✅
- No code changes required - documentation update only
- Backward compatible with 2025-03-26 and 2024-11-05

## [1.3.0] - 2025-11-08

### Added
- **Highlighting Support**: New `highlight_fields` parameter for the `search` tool
- Highlighting shows with `<em>` tags where search terms appear in results
- Highlighting support in SolrClient.search() method
- Two new unit tests for highlighting functionality
- Two new integration tests with real Solr for highlighting
- Documentation and examples for highlighting in README.md

### Changed
- Extended `search` tool with optional `highlight_fields` parameter
- Updated tool description: "Advanced search with filtering, sorting, pagination, faceting, and highlighting"
- Extended README features list with "Highlighting"
- Extended MCP Inspector guide with highlighting examples

### Technical Details
- Response now includes `highlighting` section when `highlight_fields` is provided
- Automatic setting of `hl=true`, `hl.fl`, `hl.snippets=3` and `hl.fragsize=150` in Solr query
- All 11 unit tests passing (9 existing + 2 new) ✅
- All 7 integration tests passing (5 existing + 2 new) ✅

## [1.2.0] - 2025-11-08

### Added
- **Faceted Search Support**: New `facet_fields` parameter for the `search` tool
- Automatic aggregation of field values with counts
- Facet support in SolrClient.search() method
- Two new unit tests for faceted search functionality
- Documentation and examples for faceted search in README.md

### Changed
- Extended `search` tool with optional `facet_fields` parameter
- Updated tool description: "Advanced search with filtering, sorting, pagination, and faceting"
- Extended README features list with "Faceted Search"
- Extended MCP Inspector guide with faceted search examples

### Technical Details
- Response now includes `facet_counts.facet_fields` when `facet_fields` is provided
- Automatic setting of `facet=true` and `facet.mincount=1` in Solr query
- All 7 unit tests passing ✅

## [1.1.0] - 2025-11-08

### Added
- **MCP 1.21.0 Modernization**: Full support for 2025-03-26 specification
- Lifespan Context Manager with type-safe `AppContext` dataclass
- Tool Annotations (readOnlyHint, title, description)
- Context-based logging methods (ctx.info/debug/warning/error)
- Modern FastMCP decorator pattern (@app.tool, @app.resource)
- Native Streamable HTTP transport support

### Changed
- Upgraded from MCP 1.12.3 to MCP 1.21.0
- Replaced global variables with lifespan context pattern
- Modernized function signatures (parameters first, ctx last)
- Enhanced logging with direct client communication
- Updated all unit tests for new patterns

### Removed
- MCP 1.6.0 compatibility workarounds
- FastAPI HTTP server workaround (replaced by native Streamable HTTP)
- Global variables for state management

### Technical Details
- Protocol version: 2024-11-05 → 2025-03-26
- All 5 unit tests passing ✅
- Tested with Claude Desktop integration
- Backward compatible with MCP 1.12.3 clients

## [1.0.0] - 2025-04-26

### Added
- Initial release of MCP Server for Apache Solr
- Basic search functionality via MCP resources and tools
- `search` tool with filtering, sorting, and pagination
- `get_document` tool for document retrieval by ID
- Docker Compose setup for Solr development environment
- Comprehensive test suite (unit and integration tests)
- Example documents and data loading scripts

### Technical Details
- MCP SDK: 1.6.0
- Python: 3.11+
- Apache Solr: 9.x
- All tests passing ✅

---

## Version Naming Convention

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## MCP Specification Versions

- v1.4.0: MCP Spec 2025-06-18 (OAuth 2.1 compliant)
- v1.3.1: MCP Spec 2025-06-18
- v1.3.0: MCP Spec 2025-06-18
- v1.2.0: MCP Spec 2025-03-26
- v1.1.0: MCP Spec 2025-03-26
- v1.0.0: MCP Spec 2024-11-05
