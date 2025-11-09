# OAuth 2.1 Troubleshooting Guide

This guide helps you diagnose and fix common OAuth issues with the MCP Solr Server.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Errors](#common-errors)
- [Token Issues](#token-issues)
- [Keycloak Issues](#keycloak-issues)
- [Configuration Issues](#configuration-issues)
- [Testing Tools](#testing-tools)

---

## Quick Diagnostics

### 1. Check if OAuth is properly configured

```bash
# Verify Keycloak is running
curl http://localhost:8080/health/ready

# Test OAuth flow
./test-keycloak.sh <YOUR_CLIENT_SECRET>
```

### 2. Check environment variables

```bash
# Verify .env file has correct values
cat .env | grep OAUTH
cat .env | grep KEYCLOAK
```

Expected output:
```
ENABLE_OAUTH=true
OAUTH_PROVIDER=keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=solr-mcp
KEYCLOAK_CLIENT_ID=solr-search-server
KEYCLOAK_CLIENT_SECRET=<your-secret>
OAUTH_SCOPES=solr:search,solr:read
```

### 3. Check server logs

```bash
# Start server and check for OAuth initialization
python run_server.py --mode mcp 2>&1 | grep -i oauth
```

Expected output:
```
INFO - OAuth 2.1 enabled with provider: keycloak (realm: solr-mcp)
INFO - Required scopes: ['solr:search', 'solr:read']
INFO - JWKS fetched successfully - OAuth is ready
```

---

## Common Errors

### Error: "Authentication failed: OAuth is enabled but no access token provided"

**Cause**: Tool called without `access_token` parameter when OAuth is enabled.

**Solution**:
```python
# ❌ Wrong
result = await session.call_tool("search", arguments={"query": "*:*"})

# ✅ Correct
result = await session.call_tool(
    "search",
    arguments={
        "query": "*:*",
        "access_token": "eyJhbGciOiJSUzI1NiIs..."
    }
)
```

### Error: "Authentication failed: Invalid access token"

**Causes**:
1. Token is malformed
2. Token has expired (default: 5 minutes)
3. Token was issued by wrong issuer
4. JWKS key mismatch

**Solutions**:

**1. Check token expiration:**
```bash
# Decode token and check 'exp' field
TOKEN="your-token-here"
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

Look for `"exp"` field (Unix timestamp). If expired, get a new token.

**2. Get fresh token:**
```bash
./test-keycloak.sh <CLIENT_SECRET>
# Copy the new token from output
```

**3. Verify token issuer:**
```bash
# Token should have: "iss": "http://localhost:8080/realms/solr-mcp"
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | grep iss
```

### Error: "Token missing required scopes"

**Cause**: Token doesn't have all required scopes.

**Solution**:

**1. Check which scopes are in the token:**
```bash
# View token scopes
./test-keycloak.sh <CLIENT_SECRET> | grep "Scopes:"
```

**2. Verify required scopes in .env:**
```bash
cat .env | grep OAUTH_SCOPES
# Should be: OAUTH_SCOPES=solr:search,solr:read
```

**3. Request correct scopes when getting token:**
```python
response = await client.post(
    "http://localhost:8080/realms/solr-mcp/protocol/openid-connect/token",
    data={
        # ...
        "scope": "solr:search solr:read",  # Include all required scopes
    },
)
```

**4. Verify scopes are assigned to client in Keycloak:**
```bash
# In Keycloak Admin UI:
# Clients → solr-search-server → Client scopes tab
# Ensure solr:search and solr:read are in "Assigned optional client scopes"
```

---

## Token Issues

### Token expires too quickly

**Default expiration**: 5 minutes (Keycloak default)

**Solution - Extend token lifetime in Keycloak:**

1. Open Keycloak Admin Console: http://localhost:8080
2. Go to: Realm Settings → Tokens tab
3. Adjust:
   - **Access Token Lifespan**: Change from 5 minutes to desired value (e.g., 30 minutes)
   - **Refresh Token Max Lifespan**: For using refresh tokens
4. Click "Save"

### Token validation is slow

**Cause**: Using introspection endpoint for every request.

**Solution**: Use JWKS validation (default):

```python
# Fast validation (default) - validates locally with JWKS
token_data = await validator.validate_token(token, use_introspection=False)

# Slower validation - makes HTTP request to Keycloak
token_data = await validator.validate_token(token, use_introspection=True)
```

JWKS is cached for 1 hour, making subsequent validations extremely fast.

### "Failed to fetch JWKS"

**Cause**: Can't reach Keycloak JWKS endpoint.

**Solutions**:

**1. Check Keycloak is running:**
```bash
docker-compose ps keycloak
curl http://localhost:8080/realms/solr-mcp/protocol/openid-connect/certs
```

**2. Check KEYCLOAK_URL in .env:**
```bash
# Should match where Keycloak is actually running
cat .env | grep KEYCLOAK_URL
```

**3. Check network connectivity:**
```bash
# If Keycloak is in Docker, ensure MCP server can reach it
ping localhost
```

---

## Keycloak Issues

### Keycloak container won't start

**Check logs:**
```bash
docker-compose logs keycloak
```

**Common fixes:**

**1. Port 8080 already in use:**
```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process or change Keycloak port in docker-compose.yml
```

**2. PostgreSQL not ready:**
```bash
# Check PostgreSQL health
docker-compose logs postgres

# Restart both
docker-compose restart postgres keycloak
```

**3. Complete reset:**
```bash
# Stop everything
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d keycloak
./setup-keycloak.sh
```

### Can't access Keycloak Admin Console

**URL**: http://localhost:8080

**Default credentials**: admin / admin

**If you can't log in:**

```bash
# 1. Check Keycloak is running
docker-compose ps keycloak

# 2. Check logs for errors
docker-compose logs keycloak | tail -50

# 3. Restart Keycloak
docker-compose restart keycloak

# 4. Wait 60 seconds for startup
sleep 60
curl http://localhost:8080/health/ready
```

### "Client secret is invalid"

**Get correct client secret:**

```bash
# Option 1: From Keycloak Admin UI
# Clients → solr-search-server → Credentials tab → Copy "Client secret"

# Option 2: Re-run setup script (creates new secret)
./setup-keycloak.sh

# Option 3: Check .env file
cat .env | grep KEYCLOAK_CLIENT_SECRET
```

---

## Configuration Issues

### OAuth not working after enabling in .env

**Checklist:**

1. **Restart the MCP server** after changing .env:
   ```bash
   # Stop server (Ctrl+C)
   # Start again
   python run_server.py --mode mcp
   ```

2. **Verify environment is loaded:**
   ```bash
   # Check server logs for OAuth initialization
   python run_server.py --mode mcp 2>&1 | grep "OAuth 2.1"
   ```

   Should see:
   ```
   INFO - OAuth 2.1 enabled with provider: keycloak (realm: solr-mcp)
   ```

3. **Verify .env syntax:**
   ```bash
   # No spaces around '='
   # Correct:   ENABLE_OAUTH=true
   # Wrong:     ENABLE_OAUTH = true
   ```

### Wrong scopes configured

**Symptoms:**
- Token validation succeeds but tool calls fail
- "Token missing required scopes" error

**Fix:**

1. **Check what the server requires:**
   ```bash
   cat .env | grep OAUTH_SCOPES
   # Default: OAUTH_SCOPES=solr:search,solr:read
   ```

2. **Request matching scopes when getting token:**
   ```bash
   ./test-keycloak.sh <CLIENT_SECRET>
   # Check "Scopes:" in output
   ```

3. **Verify scopes are in Keycloak:**
   - Keycloak Admin → Client Scopes
   - Should see: solr:search, solr:read, solr:write, solr:admin

---

## Testing Tools

### 1. Test OAuth flow end-to-end

```bash
# Automated test script
./test-keycloak.sh <CLIENT_SECRET>

# Should show:
# ✓ Keycloak is running
# ✓ Access token received
# ✓ Token decoded successfully
# ✓ Token is valid and active
```

### 2. Manual token testing

```bash
# Get token
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/solr-mcp/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=solr-search-server" \
  -d "client_secret=<YOUR_SECRET>" \
  -d "username=testuser" \
  -d "password=testpassword" \
  -d "grant_type=password" \
  -d "scope=solr:search solr:read" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Decode token
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool

# Validate token
curl -s -X POST "http://localhost:8080/realms/solr-mcp/protocol/openid-connect/token/introspect" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "solr-search-server:<YOUR_SECRET>" \
  -d "token=$TOKEN" \
  | python3 -m json.tool
```

### 3. Test MCP server with token

```python
import asyncio
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_oauth():
    # Get token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8080/realms/solr-mcp/protocol/openid-connect/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": "solr-search-server",
                "client_secret": "YOUR_SECRET_HERE",
                "username": "testuser",
                "password": "testpassword",
                "grant_type": "password",
                "scope": "solr:search solr:read",
            },
        )
        token = response.json()["access_token"]
        print(f"Got token: {token[:50]}...")

    # Test with MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["run_server.py", "--mode", "mcp"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # Call search with token
            result = await session.call_tool(
                "search",
                arguments={
                    "query": "*:*",
                    "rows": 5,
                    "access_token": token,
                },
            )
            print(f"Search result: {result}")

asyncio.run(test_oauth())
```

### 4. Integration tests

```bash
# Run full integration test suite
pytest tests/test_oauth_integration.py -v -m integration

# Test specific functionality
pytest tests/test_oauth_integration.py::TestKeycloakIntegration::test_validate_token_with_jwks -v
```

---

## Still Having Issues?

1. **Check the logs** - The server logs usually contain helpful error messages
2. **Run the test script** - `./test-keycloak.sh <SECRET>` tests the full OAuth flow
3. **Verify Keycloak setup** - Follow [KEYCLOAK_SETUP_GUIDE.md](KEYCLOAK_SETUP_GUIDE.md)
4. **Read the OAuth guide** - See [OAUTH_GUIDE.md](OAUTH_GUIDE.md) for implementation details
5. **Check GitHub issues** - https://github.com/mjochum64/mcp-solr-search/issues

---

**Last Updated:** 2025-11-09
**OAuth Version:** 2.1 (MCP Spec 2025-06-18)
**Keycloak Version:** 23.0

🤖 Generated with [Claude Code](https://claude.com/claude-code)
