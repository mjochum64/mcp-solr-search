# OAuth 2.1 Implementation Guide for MCP Solr Server

This document explains OAuth 2.1 requirements in MCP Specification 2025-06-18 and provides a comprehensive guide for implementation with Keycloak.

## Table of Contents

- [What is OAuth 2.1?](#what-is-oauth-21)
- [Why OAuth 2.1 in MCP 2025-06-18?](#why-oauth-21-in-mcp-2025-06-18)
- [Before vs. After Comparison](#before-vs-after-comparison)
- [How OAuth 2.1 Works](#how-oauth-21-works)
- [Implementation Impact](#implementation-impact)
- [Access Tokens Explained](#access-tokens-explained)
- [Code Changes Overview](#code-changes-overview)
- [Benefits of OAuth 2.1](#benefits-of-oauth-21)
- [Keycloak Setup](#keycloak-setup)
- [Summary](#summary)

---

## What is OAuth 2.1?

OAuth 2.1 is an **authorization** technology (not authentication!) that:
- Allows applications to **access resources on behalf of a user**
- **Without the application knowing the user's password**
- Works via time-limited **access tokens**

**Real-world example:**
When you use "Sign in with Google" on an app → That's OAuth!

**Key Principle:**
> "Don't give your password to the app, give a temporary key instead"

---

## Why OAuth 2.1 in MCP 2025-06-18?

The MCP specification evolved to require better security for production deployments:

### MCP 2025-03-26 (Previous)
- OAuth was **optional**
- Simple deployments could work without authentication
- Suitable for trusted environments only

### MCP 2025-06-18 (Current)
- OAuth 2.1 is **mandatory** for production
- Required for public/internet-facing servers
- Still optional for local development

**Rationale:**
As MCP servers become more widespread, security must be built-in from the start.

---

## Before vs. After Comparison

| Aspect | MCP 2025-03-26 | MCP 2025-06-18 |
|--------|----------------|----------------|
| **OAuth Status** | ⚠️ Optional | 🔴 **Mandatory** for Production |
| **Our Server** | ✅ Runs without auth | ❌ Production requires OAuth |
| **Local Development** | ✅ OK without auth | ✅ Still OK without auth |
| **Security** | ⚠️ Basic security | ✅ Enterprise-grade |
| **Token Validation** | Not required | Required for all requests |
| **User Permissions** | None | Fine-grained scopes |

---

## How OAuth 2.1 Works

### Current Flow (Without OAuth)
```
1. Claude Desktop starts → Our MCP Server starts
2. Claude sends: search("Python")
3. Our Server: ✅ OK, search directly
4. Solr returns results
```

**Issue:** Anyone can access! No access control.

### Future Flow (With OAuth 2.1)
```
1. Claude Desktop starts → Our MCP Server starts
2. Server says: "Please authenticate first!"
3. Claude opens browser → User logs in at OAuth Provider
   (e.g., Keycloak, Auth0, Google)
4. OAuth Provider issues Access Token
5. Claude sends: search("Python") + Access Token
6. Server validates token:
   - ✅ Token valid? → Continue
   - ✅ Has permission "solr:search"? → Continue
   - ❌ Token expired? → Error 401
   - ❌ Wrong scope? → Error 403
7. Solr returns results
8. Server logs access for audit trail
```

---

## Implementation Impact

### Scenario 1: Local Development (Current Use Case)
```
You → Claude Desktop → Our MCP Server (localhost) → Solr
```

**Status:** ✅ **Continues to work without changes!**
- Localhost is trusted
- OAuth not required for local development
- Everything works as before

**Configuration:**
```bash
# .env
ENABLE_OAUTH=false  # Default for local dev
```

---

### Scenario 2: Production Deployment (Future)
```
External Users → Claude Desktop → Our MCP Server (internet) → Solr
```

**Status:** 🔴 **OAuth 2.1 becomes REQUIRED!**

**Why?**
1. **Access Control:** Not everyone should search everything
2. **Rate Limiting:** Tokens can be rate-limited
3. **Audit Trail:** Who searched for what and when?
4. **Security:** No open APIs on the internet
5. **User Management:** Add/remove users without code changes

**Configuration:**
```bash
# .env
ENABLE_OAUTH=true
OAUTH_PROVIDER=keycloak
KEYCLOAK_URL=https://auth.example.com
KEYCLOAK_REALM=solr-mcp
KEYCLOAK_CLIENT_ID=solr-search-server
KEYCLOAK_CLIENT_SECRET=your-secret-here
```

---

## Access Tokens Explained

An access token is like a **time-limited access code**:

### Token Example (JWT Format)
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "solr:search solr:read",
  "sub": "user@example.com",
  "iat": 1699459200,
  "exp": 1699462800
}
```

**Token Decoded:**
```json
{
  "sub": "user@example.com",
  "scopes": ["solr:search", "solr:read"],
  "exp": 1699462800,
  "iat": 1699459200,
  "client_id": "solr-search-server"
}
```

**The token says:**
- ✅ This user can search (`solr:search`)
- ✅ This user can read (`solr:read`)
- ❌ This user CANNOT write
- ⏰ Token valid for 1 hour (3600 seconds)
- 👤 User: user@example.com

---

## Code Changes Overview

### Current Implementation (Without OAuth)
```python
@app.tool()
async def search(query: str, ctx: Context = None) -> Dict[str, Any]:
    """Search in Solr - ANYONE can use this!"""
    solr_client = ctx.request_context.lifespan_context.solr_client
    results = await solr_client.search(query)
    return results
```

**Issues:**
- ❌ No authentication
- ❌ No authorization
- ❌ No audit logging
- ❌ No rate limiting

---

### Future Implementation (With OAuth 2.1)
```python
from mcp.client.auth.oauth2 import OAuth2Config

# OAuth Configuration (at server startup)
oauth_config = OAuth2Config(
    authorization_endpoint="https://keycloak.example.com/realms/solr-mcp/protocol/openid-connect/auth",
    token_endpoint="https://keycloak.example.com/realms/solr-mcp/protocol/openid-connect/token",
    client_id="solr-search-server",
    client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    scopes=["solr:search", "solr:read"]
)

@app.tool()
async def search(query: str, ctx: Context = None) -> Dict[str, Any]:
    """Search in Solr - ONLY with valid token!"""

    # 1. Extract token from request
    token = ctx.request_context.auth_token

    # 2. Validate token
    if not token or not await is_token_valid(token):
        return {"error": "Unauthorized: Invalid or missing token"}

    # 3. Check permissions
    if not has_permission(token, "solr:search"):
        return {"error": "Forbidden: Missing solr:search permission"}

    # 4. Rate limiting (optional but recommended)
    if not await check_rate_limit(token):
        return {"error": "Too many requests. Try again later."}

    # 5. NOW perform the actual search
    solr_client = ctx.request_context.lifespan_context.solr_client
    results = await solr_client.search(query)

    # 6. Audit log (who searched for what)
    await log_access(token.user_id, "search", query)

    return results
```

**Benefits:**
- ✅ Token validation
- ✅ Permission checks
- ✅ Rate limiting
- ✅ Audit logging
- ✅ User identification

---

## Benefits of OAuth 2.1

### 1. Fine-Grained Permissions
```python
# User A: Read-only
scopes = ["solr:read"]

# User B: Read + Search
scopes = ["solr:read", "solr:search"]

# Admin: Everything
scopes = ["solr:read", "solr:search", "solr:write", "solr:admin"]
```

**Implementation:**
```python
# Define scopes in Keycloak
SCOPES = {
    "solr:read": "Read documents",
    "solr:search": "Search documents",
    "solr:write": "Modify documents",
    "solr:admin": "Administrative access"
}
```

---

### 2. Time-Limited Access
```python
# Token expires after 1 hour
"expires_in": 3600

# After expiration: New token required
# → Prevents stolen tokens from being used indefinitely
```

**Configuration:**
```yaml
# Keycloak token settings
access_token_lifespan: 1h
refresh_token_lifespan: 24h
```

---

### 3. Instant Revocation
```python
# Admin can immediately invalidate token
await oauth_provider.revoke_token(token)

# → User is immediately locked out
# → No server restart needed
```

**Use cases:**
- User account compromised
- Employee leaves company
- Suspicious activity detected

---

### 4. Audit Trail
```python
# Who did what and when?
2025-11-08 10:15:23 | user@example.com | search | query="Python"
2025-11-08 10:16:45 | user@example.com | search | query="Solr"
2025-11-08 10:18:12 | admin@example.com | get_document | id="doc1"
```

**Implementation:**
```python
async def log_access(user_id: str, action: str, details: str):
    logger.info(
        "AUDIT",
        extra={
            "user": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## Keycloak Setup

### Why Keycloak?

**Advantages:**
- ✅ **Open Source:** Completely free, no vendor lock-in
- ✅ **Self-Hosted:** Full control over your data
- ✅ **Powerful:** Enterprise-grade features
- ✅ **Docker-Ready:** Easy to integrate in docker-compose
- ✅ **Well-Documented:** Extensive documentation and community

**Disadvantages:**
- ⚠️ **More Complex:** Longer initial setup vs. Auth0
- ⚠️ **Own Infrastructure:** You manage it
- ⚠️ **Learning Curve:** More concepts to learn

---

### Keycloak in Docker Compose

Our project already uses Docker Compose for Solr. We can add Keycloak easily:

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  solr:
    # ... existing Solr config ...

  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    container_name: solr-mcp-keycloak
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: keycloak
      KC_HOSTNAME: localhost
      KC_HTTP_ENABLED: "true"
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    command: start-dev

  postgres:
    image: postgres:15-alpine
    container_name: solr-mcp-postgres
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: keycloak
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

### Keycloak Configuration Steps

#### 1. Start Keycloak
```bash
cd docker
docker-compose up -d keycloak postgres
```

#### 2. Access Admin Console
```
URL: http://localhost:8080
Username: admin
Password: admin
```

#### 3. Create Realm
```
1. Click "Create Realm"
2. Name: solr-mcp
3. Enabled: ON
4. Save
```

#### 4. Create Client
```
1. Go to: Clients → Create Client
2. Client ID: solr-search-server
3. Client Protocol: openid-connect
4. Client Authentication: ON
5. Authorization: OFF
6. Save
```

#### 5. Configure Client Scopes
```
1. Go to: Client Scopes → Create
2. Name: solr:search
3. Description: Allow searching in Solr
4. Type: Optional
5. Save
6. Repeat for: solr:read, solr:write, solr:admin
```

#### 6. Create Test User
```
1. Go to: Users → Add User
2. Username: testuser
3. Email: testuser@example.com
4. Email Verified: ON
5. Save
6. Go to: Credentials → Set Password
7. Password: testpassword
8. Temporary: OFF
9. Save
```

#### 7. Assign Scopes to User
```
1. Go to: Users → testuser → Client Roles
2. Select client: solr-search-server
3. Assign roles: solr:search, solr:read
4. Save
```

---

### Environment Variables

Update `.env` for OAuth with Keycloak:

```bash
# OAuth Configuration
ENABLE_OAUTH=true
OAUTH_PROVIDER=keycloak

# Keycloak Settings
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=solr-mcp
KEYCLOAK_CLIENT_ID=solr-search-server
KEYCLOAK_CLIENT_SECRET=<from-keycloak-client-credentials>

# Scopes
OAUTH_SCOPES=solr:search solr:read

# Token Validation
TOKEN_VALIDATION_ENDPOINT=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token/introspect
JWKS_ENDPOINT=${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs
```

---

## Summary

### For Local Development
✅ **No changes needed!** Everything works as before.
- OAuth can be disabled via `ENABLE_OAUTH=false`
- Suitable for development and testing

### For Production Deployment
🔴 **OAuth 2.1 is MANDATORY** as of MCP Spec 2025-06-18

**Required Components:**
1. OAuth Provider (Keycloak)
2. Token validation in MCP server
3. Permission checks in tools
4. Audit logging

**Estimated Effort:**
- With Keycloak Docker setup: **8-12 hours**
- Infrastructure setup: 2h
- Code implementation: 4h
- Testing: 2h
- Documentation: 2h

**Benefits:**
- ✅ Secure production deployment
- ✅ Access control
- ✅ Rate limiting
- ✅ Audit trail
- ✅ User management without code changes

---

## Next Steps

1. ✅ Read this guide
2. ⏭️ Review the migration roadmap in `TASK.md`
3. ⏭️ Set up Keycloak via Docker Compose
4. ⏭️ Implement OAuth in MCP server (Phase 2)
5. ⏭️ Test with real users
6. ⏭️ Deploy to production

---

**Document Version:** 1.0
**Date:** November 8, 2025
**MCP Spec:** 2025-06-18
**Author:** Claude Code

🤖 Generated with [Claude Code](https://claude.com/claude-code)
